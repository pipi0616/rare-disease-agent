# mypy: ignore-errors
"""DeepRare on one case, as published, with everything it reads kept.

This file is not imported by raredx: raredx.baselines.deeprare runs it with the
Python of DeepRare's own environment (third_party/DeepRare/.venv), which has its
dependencies (torch, transformers, Selenium) and its code. It reads one case as
JSON and writes one answer as JSON:

    python deeprare_runner.py DEEPRARE_DIR CASE.json ANSWER.json

Departures from the published setup, each forced or for cost, and stated where
results are reported:
- the model: DeepSeek deepseek-flash, thinking off, for its main model (published:
  deepseek-reasoner) and for its summariser (published: gpt-4o-mini);
- the embeddings: OpenAI text-embedding-3-small, as published, through OpenRouter —
  each case's query embedded beforehand when it can be (raredx data deeprare-queries),
  so that a long run does not depend on OpenRouter being reachable;
- the case bank: the public PubMed one (its other banks are not published);
- web search: DuckDuckGo, one of its three options and the one needing no key;
- two repairs: its DuckDuckGo tool is called with its arguments by name (it was
  called with the summariser in place of read_content), and its similar-case
  search is vectorised (the same cosine similarity, the bank parsed once).
Nothing is masked: DeepRare searches the web, PubCaseFinder, PhenoBrain and a
case bank, none of which can be masked. Every prompt it sends — which carries
everything it retrieved — is kept in the answer, so what it read can be checked.
"""

import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

MODEL = "deepseek-flash"
EMBEDDING = "openai/text-embedding-3-small"  # the model DeepRare's case bank was embedded with


def main() -> None:
    deeprare, case_file, answer_file = (Path(a).resolve() for a in sys.argv[1:4])
    sys.path.insert(0, str(deeprare))
    os.chdir(deeprare)
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import diagnosis
    import numpy as np
    import pandas as pd
    import torch
    from openai import OpenAI
    from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer
    from utils import get_disease_embeddings

    from data import RarePrompt

    case = json.loads(case_file.read_text())
    sent: list[dict] = []
    usage = {
        "model_calls": 0,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "api_errors": 0,
    }
    deepseek = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
        timeout=180,
        max_retries=5,
    )
    openrouter = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        timeout=60,
        max_retries=5,
    )

    class Model:
        """DeepRare's handler interface, on deepseek-flash."""

        def __init__(self, role):
            self.role = role

        def get_completion(self, system_prompt, prompt, seed=42):
            try:
                r = deepseek.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    extra_body={"thinking": {"type": "disabled"}},
                )
            except Exception as e:  # DeepRare expects None on failure, and carries on
                sent.append({"role": self.role, "error": repr(e)[:300]})
                usage["api_errors"] += 1
                return None
            u = r.usage
            usage["model_calls"] += 1
            usage["input_tokens"] += u.prompt_tokens
            usage["output_tokens"] += u.completion_tokens
            usage["cached_input_tokens"] += getattr(u, "prompt_cache_hit_tokens", 0) or 0
            sent.append({"role": self.role, "prompt": prompt})
            return str(r.choices[0].message.content)

    cached = {}
    if case.get("embeddings_file") and Path(case["embeddings_file"]).exists():
        cached = json.loads(Path(case["embeddings_file"]).read_text())

    def embed(text, model=None):
        if text in cached:  # embedded beforehand by the same model: no call needed
            return cached[text]
        try:
            return openrouter.embeddings.create(input=[text], model=EMBEDDING).data[0].embedding
        except Exception:
            usage["api_errors"] += 1
            raise

    args = SimpleNamespace(
        search_engine="duckduckgo",
        chrome_driver=None,
        visualize=False,
        screenshots=False,
        dataset_name="raredx",
        device=torch.device("cpu"),
        google_api="",
        search_engine_id="",
        uptodate_user="",
        uptodate_pwd="",
        results_folder=str(answer_file.parent / "deeprare-tmp"),
        gene=False,
        orpha_checkpoints="./database/embeds_concept.pt",
    )
    Path(args.results_folder, "tmp").mkdir(parents=True, exist_ok=True)
    eval_model = AutoModel.from_pretrained("FremyCompany/BioLORD-2023-C")
    eval_tok = AutoTokenizer.from_pretrained("FremyCompany/BioLORD-2023-C")
    retr_model = AutoModelForSequenceClassification.from_pretrained("ncbi/MedCPT-Cross-Encoder")
    retr_tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Cross-Encoder")
    orphanet = json.loads(
        Path("./database/orpha_disorders_HP_map.json").read_text(encoding="utf-8-sig")
    )
    concept2id = json.loads(
        Path("./database/orpha_concept2id.json").read_text(encoding="utf-8-sig")
    )
    orpha2omim = json.loads(Path("./database/orpha2omim.json").read_text(encoding="utf-8-sig"))
    bank = pd.read_csv("./database/RDS_embeddings.csv")[
        ["_id", "case_report", "embedding", "diagnosis"]
    ]
    bank = bank[bank["embedding"].notna()].reset_index(drop=True)
    vectors = np.array([json.loads(e) for e in bank["embedding"]], dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    embeds_disease = get_disease_embeddings(args, eval_model, eval_tok, concept2id)
    similar: list[str] = []

    def similar_case_search(df, product_description, embeding_handler, n=3, pprint=True):
        q = np.array(embeding_handler(product_description), dtype=np.float32)
        sims = vectors @ (q / np.linalg.norm(q))
        top = np.argsort(-sims)[:n]
        res = bank.iloc[top].copy()
        res["similarities"] = sims[top]
        similar.extend(str(i) for i in res["_id"])
        return res

    diagnosis.similar_case_search = similar_case_search
    published = diagnosis.DuckDuckGoSearchTool
    diagnosis.DuckDuckGoSearchTool = (
        lambda args, query, mini_handler, read_content=True, return_num=5: published(
            args, query, read_content=read_content, return_num=return_num, mini_handler=mini_handler
        )
    )

    started = time.time()
    patient = (", ".join(case["hpo_labels"]), "", case["hpo_labels"], case["hpo_ids"])  # query_text
    error, result = None, None
    try:
        result = diagnosis.make_diagnosis(
            args,
            0,
            patient,
            RarePrompt(),
            orphanet,
            concept2id,
            orpha2omim,
            bank,
            embeds_disease,
            eval_model,
            eval_tok,
            retr_model,
            retr_tok,
            Model("main"),
            Model("mini").get_completion,
            embed,
        )
    except Exception as e:
        error = repr(e)[:500]
        # A service it depends on could not be reached (PubCaseFinder, PhenoBrain, a model
        # API, a web page): the case is lost, not answered wrong. requests' errors are OSErrors.
        reached = (type(e).__module__ or "").split(".")[0]
        if isinstance(e, OSError) or reached in (
            "requests",
            "urllib3",
            "openai",
            "httpx",
            "selenium",
        ):
            usage["api_errors"] += 1
    final = (result or {}).get("final_diagnois")
    answer = {
        "final": final,
        "error": error if final is None else None,
        "seconds": round(time.time() - started, 1),
        "usage": usage,
        "read": {
            "prompts": [s.get("prompt") or s.get("error") for s in sent],
            "similar_cases": similar,
            "diagnosis_tools": (result or {}).get("diagnosis_api_response"),
        },
    }
    answer_file.write_text(json.dumps(answer, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
