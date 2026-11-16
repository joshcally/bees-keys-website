import sys, cv2, numpy as np
src, dst, dbg = sys.argv[1:4]
im = cv2.imread(src)                      # BGR 1536x1024
h, w = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
Hh, Ss, Vv = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2]
warm = (Hh < 44) & (Ss > 0.5)                       # red / orange leaves, flower centres
yellow = (Hh < 56) & (Vv > 222) & (Ss > 0.55)       # yellow petals
white = (Ss < 0.32) & (Vv > 190)                    # daisies
m = (warm | yellow | white)
m[: int(h * 0.60)] = False                          # foreground meadow only
m = m.astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
# flowers: stretch the mask downward over stems and leaves
fl = ((yellow | white) & (m > 0)).astype(np.uint8)
stem = cv2.dilate(fl, np.ones((120, 36), np.uint8), anchor=(18, 119))
m = cv2.dilate(m | stem, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (23, 23)))
m[: int(h * 0.60)] = 0
# fill: normalised blur of the unmasked grass, then feather
keep = (1 - m).astype(np.float32)
k = (0, 0)
num = cv2.GaussianBlur(im.astype(np.float32) * keep[..., None], k, 22)
den = cv2.GaussianBlur(keep, k, 22)[..., None]
fill = num / np.maximum(den, 1e-3)
num2 = cv2.GaussianBlur(im.astype(np.float32) * keep[..., None], k, 80)
den2 = cv2.GaussianBlur(keep, k, 80)[..., None]
t = np.clip(den / 0.25, 0, 1)
fill = fill * t + (num2 / np.maximum(den2, 1e-3)) * (1 - t)
rng = np.random.default_rng(3)
fill += cv2.GaussianBlur(rng.normal(0, 5, (h, w, 1)).astype(np.float32), k, 1.2)[..., None]
a = cv2.GaussianBlur(m.astype(np.float32), k, 7)[..., None]
out = im * (1 - a) + fill * a
cv2.imwrite(dst, np.clip(out, 0, 255).astype(np.uint8))
d = im.copy(); d[m > 0] = (255, 0, 255)
cv2.imwrite(dbg, cv2.resize(d, (1200, 800)))
cv2.imwrite(dbg.replace("mask", "out"), cv2.resize(np.clip(out, 0, 255).astype(np.uint8), (1200, 800)))
