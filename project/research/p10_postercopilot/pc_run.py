"""Run the PosterCopilot checkpoint on layer folders with a quantised load (this machine has 16 GB VRAM, the card asks ~20 GB in bf16).
Same preprocessing, prompt and decoding as the reference predictor (vendor postercopilot/predictor.py, read 2026-11-15); only the load differs.

  pc_run.py VENDOR MODEL MODE JOBS.json      MODE: 8bit | 4bit | bf16      JOBS: [{"assets": dir, "width": px, "height": px, "out": file, "requirement": ""}]
"""
import json
import sys
import time
from pathlib import Path

vendor, model_path, mode, jobs_file = sys.argv[1:5]
sys.path.insert(0, vendor)
import torch  # noqa: E402
from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2_5_VLForConditionalGeneration  # noqa: E402
from postercopilot.assets import discover_assets  # noqa: E402
from postercopilot.constants import LAYER_MAX_PIXELS, LAYER_MIN_PIXELS, TOKENS_OVERHEAD, TOKENS_PER_LAYER  # noqa: E402
from postercopilot.image_processing import load_layer_images  # noqa: E402
from postercopilot.postprocess import LayoutParseError, attach_asset_index, extract_layout_json, normalize_layout, validate_layout  # noqa: E402
from postercopilot.prompts import build_messages  # noqa: E402

kw = {"dtype": torch.bfloat16, "attn_implementation": "sdpa"}
if mode == "8bit":
    kw.update(quantization_config=BitsAndBytesConfig(load_in_8bit=True), device_map={"": 0})
elif mode == "4bit":
    kw.update(quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16), device_map={"": 0})
else:
    kw.update(device_map="auto", max_memory={0: "13GiB", "cpu": "24GiB"})
t0 = time.time()
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_path, **kw).eval()
model.generation_config.do_sample = False
model.generation_config.temperature = None
proc = AutoProcessor.from_pretrained(model_path, min_pixels=LAYER_MIN_PIXELS, max_pixels=LAYER_MAX_PIXELS, use_fast=False)
print(f"loaded {mode} in {time.time() - t0:.0f}s, vram {torch.cuda.memory_allocated() / 2**30:.1f} GiB", flush=True)

for job in json.loads(Path(jobs_file).read_text(encoding="utf-8")):
    assets = discover_assets(job["assets"])
    w, h = job["width"], job["height"]
    images = load_layer_images([a.path for a in assets], min_pixels=LAYER_MIN_PIXELS, max_pixels=LAYER_MAX_PIXELS)
    text = proc.apply_chat_template(build_messages(len(images), w, h, job.get("requirement", "")), tokenize=False, add_generation_prompt=True)
    inputs = proc(text=text, images=images, return_tensors="pt", padding=True).to("cuda:0").to(torch.bfloat16)
    eos = proc.tokenizer.eos_token_id
    t = time.time()
    with torch.inference_mode():
        gen = model.generate(**inputs, max_new_tokens=TOKENS_PER_LAYER * len(assets) + TOKENS_OVERHEAD, do_sample=False, use_cache=True,
                             repetition_penalty=1.05, pad_token_id=eos, eos_token_id=eos)
    new = gen[0][inputs.input_ids.shape[1]:]
    raw = proc.tokenizer.decode(new, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        layout = normalize_layout(extract_layout_json(raw), w, h)
        warns = validate_layout(layout, assets)
        attach_asset_index(layout, assets)
        out.write_text(json.dumps(layout, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{job['assets']}: {len(assets)} layers, {int(new.shape[0])} tokens, {time.time() - t:.1f}s, warnings={warns}", flush=True)
    except LayoutParseError as ex:
        out.with_suffix(".raw.txt").write_text(raw, encoding="utf-8")
        print(f"{job['assets']}: PARSE_FAILED {ex}", flush=True)
