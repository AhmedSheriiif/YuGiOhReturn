"""Transcribe Joey's voice lines (extracted/voice/.../internal/joey_*.wav) with Whisper."""
import glob, os, json, whisper
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'extracted', 'voice', 'joey', 'english', 'internal')
model = whisper.load_model('small.en', download_root=r'D:\YugiohReturn\models')
out = {}
for p in sorted(glob.glob(os.path.join(SRC, 'joey_*.wav'))):
    r = model.transcribe(p, language='en', fp16=True)
    out[os.path.basename(p)] = r['text'].strip()
    print(os.path.basename(p), '|', out[os.path.basename(p)], flush=True)
json.dump(out, open(os.path.join(os.path.dirname(HERE), 'docs', 'joey_voice_lines.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
