import cv2
import numpy as np
import mss
import time
import os

templates = {}
for name in range(10):
    templates[str(name)] = cv2.imread(f"assets/digits/{name}.png", cv2.IMREAD_GRAYSCALE)
templates["empty"] = cv2.imread("assets/digits/empty.png", cv2.IMREAD_GRAYSCALE)

screen_region = (730, 276, 39, 18)

# ---------- CONFIG ----------
TEMPLATES_DIR = "assets/digits"
SCREEN_REGION = (730, 276, 39, 18)  # (left, top, width, height)
DIGIT_W = 13
DIGIT_H = 18
EMPTY_FRAC_THRESH = 0.02   # if <2% white pixels => consider slot empty
ACCEPT_SCORE_MIN = 0.30    # if best score < this, warn (still returns best)
DEBUG = False
# ----------------------------

# Local bindings for speed
_cvt = cv2.cvtColor
_inRange = cv2.inRange
_countNonZero = cv2.countNonZero
_bitwise_xor = cv2.bitwise_xor
_BGRA2BGR = cv2.COLOR_BGRA2BGR
_BGR2HSV = cv2.COLOR_BGR2HSV

# Load and preprocess templates once (grayscale, binary, correct size)
templates_bin = []   # list of (name_str, binary_uint8_array)
empty_template = None

for name in list(map(str, range(10))) + ["empty"]:
    path = os.path.join(TEMPLATES_DIR, f"{name}.png")
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Template not found: {path}")
    # resize to exact slot size (nearest to preserve binary look)
    if img.shape != (DIGIT_H, DIGIT_W):
        img = cv2.resize(img, (DIGIT_W, DIGIT_H), interpolation=cv2.INTER_NEAREST)
    _, img_bin = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    if name == "empty":
        empty_template = img_bin
    else:
        templates_bin.append((name, img_bin))

if empty_template is None:
    raise RuntimeError("empty template missing")

# Precompute slot starts
SLOT_STARTS = (0, 13, 26)

def split_slots_from_mask(mask, digit_w=DIGIT_W):
    """Return three 13xH slices; pad with zeros if needed."""
    h, w = mask.shape[:2]
    out = []
    for s in SLOT_STARTS:
        e = s + digit_w
        if s >= w:
            crop = np.zeros((h, digit_w), dtype=mask.dtype)
        else:
            crop = mask[:, s: min(e, w)]
            if crop.shape[1] < digit_w:
                pad = np.zeros((h, digit_w - crop.shape[1]), dtype=mask.dtype)
                crop = np.concatenate((crop, pad), axis=1)
        out.append(crop)
    return out

def capture(region, templates_prepped=templates_bin,
                     digit_w=DIGIT_W, debug=DEBUG):
    """Capture region and return recognized integer (fast, monolithic)."""
    # capture
    with mss.mss() as sct:
        shot = sct.grab({"left": region[0], "top": region[1],
                         "width": region[2], "height": region[3]})
        arr = np.asarray(shot)  # BGRA
    img_bgr = _cvt(arr, _BGRA2BGR)

    # mask whites (single-channel binary 0/255)
    hsv = _cvt(img_bgr, _BGR2HSV)
    mask = _inRange(hsv, np.array([0,0,200], dtype=np.uint8), np.array([179,40,255], dtype=np.uint8))

    # split into slots
    slots = split_slots_from_mask(mask, digit_w=digit_w)

    recognized = []
    for i, slot in enumerate(slots):
        # slot is already single-channel binary 0/255 from mask
        nonzero = _countNonZero(slot)
        frac = nonzero / slot.size

        if frac < EMPTY_FRAC_THRESH:
            recognized.append("empty")
            if debug:
                print(f"[slot {i}] empty (frac={frac:.4f})")
            continue

        # compare against all digit templates using XOR mismatch ratio
        best_score = -1.0
        best_digit = None

        for name, t_bin in templates_prepped:
            # t_bin is already (DIGIT_H, DIGIT_W) and binary
            # slot and t_bin shapes should match
            # XOR and count mismatches
            diff = _bitwise_xor(slot, t_bin)
            mismatched = _countNonZero(diff)
            score = 1.0 - (mismatched / slot.size)
            if score > best_score:
                best_score = score
                best_digit = name

        if debug:
            note = "(UNCERTAIN)" if best_score < ACCEPT_SCORE_MIN else ""
            print(f"[slot {i}] best={best_digit} score={best_score:.3f} frac={frac:.4f} {note}")

            # write debug images if requested
            cv2.imwrite(f"dbg_slot_{i}.png", slot)
            cv2.imwrite(f"dbg_best_{i}.png", next(t for n,t in templates_prepped if n==best_digit))
            cv2.imwrite(f"dbg_diff_{i}.png", _bitwise_xor(slot, next(t for n,t in templates_prepped if n==best_digit)))

        recognized.append(best_digit if best_digit is not None else "empty")

    # numbers grow to the right: strip leading empties (left side)
    while recognized and recognized[0] == "empty":
        recognized.pop(0)

    if not recognized:
        return 0

    # join digits -> integer
    try:
        return int("".join(recognized))
    except ValueError:
        # fallback: build only digits (ignore any unexpected names)
        digits_only = [d for d in recognized if d is not None and d.isdigit()]
        return int("".join(digits_only)) if digits_only else 0

if __name__ == "__main__":
    prev = None
    while True:
        val = capture(SCREEN_REGION, templates_bin, digit_w=DIGIT_W, debug=False)
        # print only on change to reduce console spam (but prints every sec if you prefer)
        if val != prev:
            print(f"Current value: {val}")
            prev = val
        time.sleep(1.0)
