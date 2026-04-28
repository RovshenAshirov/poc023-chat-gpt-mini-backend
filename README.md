
# POC-023 — Bosqich 1: Asosiy Tushunchalar
> **Maqsad:** LLM inferfeysini tushunish uchun zarur bo'lgan texnik asoslar.
 
---
 
## 1. Token nima?
 
LLM matn bilan ishlamasdan oldin — matnni **kichik bo'laklarga** bo'ladi.
Bu bo'laklar **token** deyiladi.
 
```
"Assalomu alaykum" → ["Ass", "alom", "u", " al", "ayk", "um"]
                           ↑ 6 ta token
 
"Toshkent" → ["Tosh", "kent"]
                  ↑ 2 ta token
```
 
Token ≈ so'zning bir qismi. Ba'zan butun so'z, ba'zan yarim so'z.
 
---
 
## 2. Embedding nima? (Token → Vektor)
 
Token — bu faqat matn. Kompyuter matn bilan hisob-kitob qila olmaydi.
Shuning uchun har bir token **vektorga** aylanadi — sonlar ro'yxatiga.
 
```
"Salom"    → [0.23, -0.87, 0.45, 0.12, ... 768 ta son]
"Assalom"  → [0.21, -0.85, 0.44, 0.11, ... 768 ta son]  ← o'xshash!
"Xayr"     → [-0.54, 0.33, -0.21, 0.67, ... 768 ta son] ← boshqacha!
"Uy"       → [0.87, 0.12, -0.67, 0.34, ... 768 ta son]  ← umuman boshqa!
```
 
**Muhim:** O'xshash ma'noli so'zlar → o'xshash sonlar.
Bu jarayon **Embedding** deyiladi.
 
---
 
## 3. Matritsa ko'paytirish nima? (LLM hisob-kitobining asosi)
 
Vektor tayyor. Endi nima qiladi?
 
Model ichida **katta sonlar jadvali** — matritsa bor.
Vektor shu matritsa bilan **ko'paytiriladi**:
 
```
"Salom" vektori:        Model matritsasi:
[0.23, -0.87, 0.45] ×  [w1, w2, w3]   =   yangi vektor
                        [w4, w5, w6]
                        [w7, w8, w9]
```
 
Bu ko'paytirish **ma'lumotni boyitadi** — so'zning ma'nosini chuqurlashtiradi.
 
### Nima uchun millionlab ko'paytirish?
 
```
1 ta "Salom" uchun:
→ 768 × 768 matritsa = 589,824 ko'paytirish
→ 18 qatlam × 589,824 = ~10 million ko'paytirish
→ Faqat 1 token uchun!
```
 
---
 
## 4. CPU nima?
 
**CPU = Central Processing Unit** — kompyuterning "miyasi".
 
```
├── 4–16 ta kuchli yadro
├── Har bir yadro murakkab ishlarni qila oladi
└── Ketma-ket ishlaydi: 1 → 2 → 3 → 4 → 5
```
 
CPU yadrosi ichida **juda ko'p narsa** bor:
 
```
Bitta CPU yadrosi:
├── Branch predictor   → "keyingi buyruq qaysi?" deb taxmin qiladi
├── Cache (L1,L2,L3)   → tez-tez ishlatiladigan ma'lumotlarni yaqin saqlaydi
├── Out-of-order engine → buyruqlarni qayta tartiblab tezlashtiradi
└── ALU                → matematik amallar
 
→ Juda murakkab = katta joy egallaydi
→ Chipga 4–16 ta sig'adi
```
 
---
 
## 5. GPU nima?
 
**GPU = Graphics Processing Unit** — dastlab o'yinlar uchun yaratilgan.
 
```
├── Minglab kichik yadro (RTX 2050 da ~2048 ta)
├── Har bir yadro FAQAT oddiy hisob-kitob qiladi
└── Hammasi bir vaqtda ishlaydi: 1, 2, 3, 4, 5
```
 
GPU yadrosi ichida **juda kam narsa** bor:
 
```
Bitta GPU yadrosi:
└── ALU → faqat 2+2=4, xolos
 
→ Juda oddiy = juda kichik joy egallaydi
→ Chipga 2048+ ta sig'adi
```
 
---
 
## 6. CPU vs GPU — farq nimada?
 
```
CPU:  1 → 2 → 3 → 4 → 5     (ketma-ket, lekin kuchli)
GPU:  1, 2, 3, 4, 5           (bir vaqtda, parallel)
```
 
### Oshpaz misoli
 
```
CPU = 4 ta tajribali oshpaz
├── Har biri: plov, lag'mon, sho'rva — barchasini pishira oladi
└── 100 ta buyurtma → navbat uzun 😤
 
GPU = 2048 ta oddiy oshpaz
├── Har biri: FAQAT kartoshka qovuradi
└── 2048 ta kartoshka → 1 daqiqada tayyor 🚀
```
 
### LLM uchun qaysi biri kerak?
 
```
LLM hisob-kitoblari = matritsa ko'paytirish
                    = bir xil oddiy amal, millionlab marta
 
CPU (16 yadro):   589,824 ÷ 16    = 36,864 qadam
GPU (2048 yadro): 589,824 ÷ 2048  = 288 qadam
 
→ GPU ~100x tezroq! ✅
```
 
### CPU parallel ishlay oladimi?
 
Ha, ishlay oladi. Lekin farq bor:
 
```
CPU parallel = Task Parallelism
├── Har xil vazifalar bir vaqtda
└── Chrome + Spotify + VS Code = 3 ta har xil ish
 
GPU parallel = Data Parallelism
├── Bir xil vazifa, har xil ma'lumot
└── 2048 ta ko'paytirish = 2048 ta bir xil ish
 
LLM = bir xil hisob-kitob, millionlab marta
→ GPU uchun tug'ilgan vazifa ✅
```
 
---
 
## 7. VRAM nima?
 
GPU ning **o'z xotirasi** — RAM ga o'xshash, lekin GPU uchun.
 
```
RAM   → CPU ishlatadi  → bizda 30 GB
VRAM  → GPU ishlatadi  → bizda 4 GB ⚠️
```
 
Model ishlashi uchun **butun model VRAM ga sig'ishi** kerak:
 
```
VRAM sarfi = model og'irliklari + KV Cache + aktivatsiyalar
 
gemma3:1b   = 778 MB  → 4 GB ga sig'adi   ✅ → GPU da ishlaydi
gemma4:e4b  = 9.6 GB  → 4 GB ga sig'maydi ❌ → CPU ga tushadi → sekin
```
 
---
 
## 8. CUDA nima?
 
GPU dastlab faqat o'yin grafikalari uchun edi.
Olimlar uni hisob-kitodlarda ishlatmoqchi bo'lganda muammo paydo bo'ldi:
 
```
CUDAsiz:    Python → grafik API → GPU   (juda qiyin) 😤
CUDA bilan: Python → CUDA → GPU        (oson, qulay) ✅
```
 
**CUDA = CPU va GPU o'rtasidagi ko'prik** (NVIDIA, 2006).
 
### Django bilan taqqoslash
 
```
GPU hardware  =  PostgreSQL
CUDA          =  psycopg2 (Python ↔ PostgreSQL ko'prigi)
PyTorch/vLLM  =  Django ORM (psycopg2 ni ichida ishlatadi)
```
 
Siz Django da to'g'ridan-to'g'ri SQL yozmayssiz.
Xuddi shunday, vLLM to'g'ridan-to'g'ri CUDA yozmaydi.
 
### Qatlamlar
 
```
vLLM / PyTorch  (sizning kod)
      ↓
    CUDA
      ↓
 NVIDIA Driver
      ↓
  GPU Hardware (RTX 2050)
```
 
---
 
## 9. LLM nima?
 
**LLM = Large Language Model = Katta Til Modeli**
 
Aslida — **matn bashorat qiluvchi dastur**.
 
### Ichida nima bor?
 
```
gemma3:1b = 1 milliard parametr
          = 1,000,000,000 ta son
          = xotirada saqlangan "bilim"
 
w[0]         =  0.823
w[1]         = -0.445
w[2]         =  0.112
...
w[999999999] =  0.234
```
 
"Toshkent", "V asr" — hech qayerda yozilmagan. Faqat sonlar.
 
### Qanday bashorat qiladi?
 
```
Siz:   "Salom, qanday..."
Model: keyingi token nima bo'lishi mumkin?
 
"yuribsiz"   → 71%  ← eng yuqori → tanlanadi ✅
"holatdasiz" → 18%
"ketayapsiz" →  8%
...boshqalar →  3%
```
 
Bu jarayon **har bir yangi token uchun** takrorlanadi.
 
---
 
## 10. Transformer arxitekturasi nima?
 
2017 yil Google **"Attention Is All You Need"** maqolasini chiqardi.
Shu maqolada Transformer arxitekturasi taklif qilindi.
 
### Undan oldin — RNN muammosi
 
```
RNN (eski usul):
"Men" → "yillar" → "oldin" → "Toshkentda" → "o'qigan" → "maktabim"
                                                                ↑
                                              "Men" ni unutgan! 😅
```
 
### Transformer yechimi — Attention
 
Transformer **barchasini bir vaqtda** ko'radi:
 
```
"Men yillar oldin Toshkentda o'qigan maktabim"
  ↑______________________________________________↑
  ↑____________________↑
  ↑_________↑
 
Har bir so'z → boshqa BARCHA so'zlar bilan bog'lanadi
"maktabim" + "Men" = bog'liq! ✅
```
 
---
 
## 11. Attention mexanizmi nima?
 
Attention — har bir token **boshqa tokenlarga qanchalik e'tibor berishi** kerakligini hisoblaydi.
 
```
"Toshkent qachon qurilgan?"
 
"qurilgan" so'zi kimga e'tibor beradi?
→ "Toshkent" ga: 85%  ← asosiy mavzu!
→ "qachon"   ga: 12%  ← vaqt so'ralayapti
→ "?"        ga:  3%
→ boshqalar  ga:  0%
```
 
### Matematik jihatdan
 
Har token uchun 3 ta vektor yaratiladi:
 
```
Q (Query)  = "men nimani qidiryapman?"
K (Key)    = "menda nima bor?"
V (Value)  = "topilsa nima beraman?"
 
Q × K = e'tibor darajasi (qaysi tokenlarga qarayman?)
e'tibor × V = yangi boyitilgan vektor
```
 
---

## 12. KV Cache nima?
 
### Muammo
 
Attention ishlashi uchun — har yangi token uchun **oldingi barcha tokenlar** qayta hisoblanadi:
 
```
Token 1: [t1] hisobla
Token 2: [t1, t2] hisobla       ← t1 qayta hisoblanadi! 😤
Token 3: [t1, t2, t3] hisobla   ← t1, t2 qayta hisoblanadi! 😤
```
 
### Yechim — KV Cache
 
Hisob-kitob natijalarini **xotirada saqlash**:
 
```
Token 1: [t1] hisobla → cache ga saqlash
Token 2: cache + [t2]  ← t1 qayta hisoblanmaydi ✅
Token 3: cache + [t3]  ← t1,t2 qayta hisoblanmaydi ✅
```
 
Natija — **3–5x tezroq!**
 
### Muammo — xotira isrof
 
```
Oddiy tizim:
"Bu so'rov 2048 token bo'lishi mumkin"
→ 2048 token uchun joy band qil
 
Amalda: foydalanuvchi 200 token yozdi
→ 1848 token joy = BO'SH, ISROF! 😤
→ VRAM ning 60–80% bekorga ketadi
```
 
---

## 13. PagedAttention nima?
 
---
 
Bir nechta foydalanuvchi bir vaqtda so'rov yubordi:
 
```
Foydalanuvchi 1: "Salom"               → 2 token
Foydalanuvchi 2: "Toshkent haqida ayt" → 4 token
Foydalanuvchi 3: "Ha"                  → 1 token
```
 
---
 
### Oddiy KV Cache qanday ishlaydi?
 
Har foydalanuvchi uchun **oldindan** maksimum joy ajratiladi.
 
Nima uchun maksimum? — Foydalanuvchi keyinchalik ko'proq yozishi mumkin,
tizim qancha yozishini bilmaydi. Shuning uchun ehtiyot uchun 2048 token
uchun joy band qiladi.
 
```
VRAM (4 GB):
 
Foydalanuvchi 1 keldi:
┌─────────────────────────────────────────────────┐
│ [token1][token2][  bo'sh  bo'sh  bo'sh  bo'sh  ]│
│          2 token    ←————— 2046 token bo'sh ————→│
└─────────────────────────────────────────────────┘
 
Foydalanuvchi 2 keldi:
┌─────────────────────────────────────────────────┐
│ [t1][t2][t3][t4][  bo'sh  bo'sh  bo'sh  bo'sh  ]│
│    4 token     ←————— 2044 token bo'sh ————————→│
└─────────────────────────────────────────────────┘
 
Foydalanuvchi 3 keldi:
┌─────────────────────────────────────────────────┐
│ [token1][  bo'sh  bo'sh  bo'sh  bo'sh  bo'sh   ]│
│  1 token  ←—————— 2047 token bo'sh ————————————→│
└─────────────────────────────────────────────────┘
 
Foydalanuvchi 4 keldi → JOY QOLMADI! ❌
```
 
Haqiqat:
```
Ajratildi:   3 × 2048 = 6144 token joy
Ishlatildi:  2 + 4 + 1 = 7 token
Isrof:       6137 token joy → VRAM ning ~99% bekorga! 😤
```
 
---
 
### PagedAttention qanday hal qiladi?
 
**Linux virtual xotira** tizimidan ilhomlanib yaratilgan.
 
Linux RAM ni kichik **sahifalarga** bo'lib boshqaradi:
- Har dastur faqat kerakli sahifalarni oladi
- Sahifalar ketma-ket bo'lishi **shart emas**
- Bo'sh sahifalar darhol boshqaga beriladi
PagedAttention xuddi shu g'oyani KV Cache ga qo'lladi.
 
---
 
### PagedAttention qanday ishlaydi?
 
VRAM kichik **sahifalarga** bo'lingan (har sahifa = 16 token):
 
```
VRAM bo'sh holda:
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ S1 │ S2 │ S3 │ S4 │ S5 │ S6 │ S7 │ S8 │ S9 │S10 │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
  bo'sh sahifalar
```
 
Foydalanuvchi 1 keldi — 2 token yozdi → **1 sahifa** oldi:
 
```
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ F1 │    │    │    │    │    │    │    │    │    │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
```
 
Foydalanuvchi 2 keldi — 4 token yozdi → **1 sahifa** oldi:
 
```
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ F1 │ F2 │    │    │    │    │    │    │    │    │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
```
 
Foydalanuvchi 3 keldi — 1 token yozdi → **1 sahifa** oldi:
 
```
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ F1 │ F2 │ F3 │    │    │    │    │    │    │    │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
```
 
Foydalanuvchi 1 ko'proq yozdi — sahifasi to'ldi → **yangi sahifa** oldi:
 
```
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ F1 │ F2 │ F3 │ F1 │    │    │    │    │    │    │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
  ↑                  ↑
  F1 ning 1-sahifasi  F1 ning 2-sahifasi
  (ketma-ket emas — muammo yo'q!) ✅
```
 
Foydalanuvchi 4 keldi → bo'sh sahifa bor → **darhol joy oladi**:
 
```
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ F1 │ F2 │ F3 │ F1 │ F4 │    │    │    │    │    │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
```
 
---
 
### Taqqoslash
 
```
Oddiy KV Cache:
┌──────────────────┬──────────────────┬──────────────────┐
│F1: ██░░░░░░░░░░░░│F2: ████░░░░░░░░░░│F3: █░░░░░░░░░░░░░│
│  2/2048 token    │   4/2048 token   │   1/2048 token   │
└──────────────────┴──────────────────┴──────────────────┘
█ = ishlatilgan    ░ = bo'sh, isrof
Isrof: ~99% 😤
 
PagedAttention:
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ F1 │ F2 │ F3 │ F1 │ F4 │ F2 │ F3 │ F1 │
└────┴────┴────┴────┴────┴────┴────┴────┘
Isrof: ~4% ✅
```

--

## 14. Qatlam (Layer) nima? Nima uchun 18 ta?
 
### Bir qatlam yetmaydi
 
```
"Men kecha bankka bordim, u yerda navbat ko'p edi"
                              ↑
                          "u" = kim? bank? men?
→ Butun gapni ko'rish kerak → 1 qatlam yetmaydi
```
 
### Har qatlam nimani tushunadi?
 
```
Qatlam 1–3:   So'zlar, grammatika
              "qurilgan" = o'tgan zamon, passiv fe'l
 
Qatlam 4–8:   Ma'no, bog'liqlik
              "Toshkent" = O'zbekiston poytaxti, shahar
 
Qatlam 9–14:  Kontekst, mantiq
              "qachon qurilgan" = tarixiy savol
 
Qatlam 15–18: Bilim, xulosa
              "Toshkent tarixi" → "V asr" → javob tayyor
```
 
### Qatlam ichida nima bor?
 
Har bir qatlam **2 ta blokdan** iborat:
 
```
┌──────────────────────────────────┐
│  1. Attention bloki              │
│     "Tokenlar bir-birini ko'radi"│
│     Q, K, V vektorlar            │
├──────────────────────────────────┤
│  2. Feed Forward bloki           │
│     "Bilimni qo'llaydi"          │
│     Model xotirasidan ma'lumot   │
└──────────────────────────────────┘
```
 
### Qancha qatlam — shuncha aqlli
 
```
gemma3:1b   → 18 qatlam  → oddiy savollar
gemma3:4b   → 34 qatlam  → murakkab savollar
gemma4:e4b  → 62 qatlam  → juda murakkab savollar
GPT-4       → 96 qatlam  → eng murakkab savollar
```
 
---
  
## 15. "Toshkent qachon qurilgan?" — to'liq jarayon
 
```
Siz: "Toshkent qachon qurilgan?"
```
 
### Qadam 1 — Tokenizatsiya
 
```
→ ["Tosh", "kent", " qach", "on", " quril", "gan", "?"]
       ↑ 7 ta token
```
 
### Qadam 2 — Embedding
 
```
"Tosh"   → [0.67, -0.12, 0.88, ...]  768 ta son
"kent"   → [0.45,  0.33, 0.71, ...]  768 ta son
"qach"   → [0.12, -0.55, 0.34, ...]  768 ta son
...
```
 
### Qadam 3 — Attention
 
```
"Tosh" + "kent" → "Toshkent" = shahar
"qach" + "on"   → "qachon"   = vaqt savoli
"quril" + "gan" → "qurilgan" = tarix
 
Model tushunadi: "Toshkent shahrining qurilish vaqti so'ralayapti"
```
 
### Qadam 4 — 18 qatlam orqali o'tish
 
```
[vektor] → Qatlam 1  → "so'zlar tanildi"
         → Qatlam 5  → "Toshkent = shahar"
         → Qatlam 10 → "tarixiy savol"
         → Qatlam 15 → "V asr, miloddan avval"
         → Qatlam 18 → "javob tayyor"
```
 
### Qadam 5 — Bashorat (32,000 token ga ball)
 
```
"V"          → 8.91  ← eng yuqori!
"IV"         → 3.21
"VI"         → 2.10
"miloddan"   → 1.43
...
32,000 ta token
```
 
### Qadam 6 — Softmax → ehtimollik
 
```
"V"    → 89%  ← tanlanadi ✅
"IV"   →  7%
"VI"   →  3%
"VII"  →  1%
```
 
### Qadam 7 — Qayta kiritiladi
 
```
"Toshkent qachon qurilgan?" + "V"
                                ↓ yana 18 qatlam
                           "asrda" → 94% ✅
 
"Toshkent qachon qurilgan?" + "V asrda"
                                ↓ yana 18 qatlam
                           "qurilgan" → 87% ✅
...
[STOP] belgisi chiqqunga qadar davom etadi
```
 
### Natija
 
```
"V asrda qurilgan." ✅
 
Jami: 5 ta bashorat
      Har biri uchun: ~10 million ko'paytirish
      Jami: ~50 million ko'paytirish
```
 
---
 
## 16.  LLM qanday qilib butun gap chiqaradi?

---

### LLM faqat 1 ta ish qiladi

```
Kirish → 18 qatlam → 1 ta yangi token
```

Faqat **1 ta token** chiqaradi. Ko'p emas.

---

### Unda qanday qilib butun gap chiqadi?

Qayta-qayta ishga tushiradi. Har safar **1 ta token** qo'shib.

---

### Bosqichma-bosqich

```
1-ishga tushirish:
Kirish:  "Toshkent qachon qurilgan?"
Chiqish: "V"

                    ↓ chiqish → kirishga qo'shiladi

2-ishga tushirish:
Kirish:  "Toshkent qachon qurilgan? V"
Chiqish: "asrda"

                    ↓ chiqish → kirishga qo'shiladi

3-ishga tushirish:
Kirish:  "Toshkent qachon qurilgan? V asrda"
Chiqish: "qurilgan"

                    ↓ chiqish → kirishga qo'shiladi

4-ishga tushirish:
Kirish:  "Toshkent qachon qurilgan? V asrda qurilgan"
Chiqish: "."

                    ↓ chiqish → kirishga qo'shiladi

5-ishga tushirish:
Kirish:  "Toshkent qachon qurilgan? V asrda qurilgan."
Chiqish: [STOP] ← to'xtash belgisi

                    ↓ [STOP] chiqdi → loop to'xtaydi

Natija: "V asrda qurilgan."
```

---

### [STOP] nima?

Model lug'atida oddiy tokenlar bilan birga **maxsus token** bor:

```
Token 0:     "the"
Token 1:     "salom"
Token 2:     "men"
...
Token 32000: [STOP] ← "gap tugadi" belgisi
```

Model shu tokenni chiqarsa — loop to'xtaydi.

---

## KV Cache bu yerda qanday yordam beradi?

Har ishga tushirishda — oldingi tokenlar **qayta hisoblanmaydi**:

```
1-ishga tushirish:
"Toshkent qachon qurilgan?"
→ hamma tokenlar hisoblanadi → cache ga saqlanadi

2-ishga tushirish:
"Toshkent qachon qurilgan? V"
→ oldingilar cache dan olinadi ✅
→ faqat "V" hisoblanadi

3-ishga tushirish:
"Toshkent qachon qurilgan? V asrda"
→ oldingilar cache dan olinadi ✅
→ faqat "asrda" hisoblanadi
```

KV Cache bo'lmasa — har safar hammasi qayta hisoblanadi → juda sekin! 😤

---

## 17. Nega "V" ni topdi, "VI" emas?
 
Model **bilmaydi** — faqat **bashorat** qiladi.
 
### O'qitishda nima bo'ldi?
 
```
Internet + kitoblar + Wikipedia:
"Toshkent miloddan avval V asrda qurilgan" → 847,000 marta
"Toshkent miloddan avval VI asrda qurilgan" →   3,200 marta
```
 
Har safar noto'g'ri bashorat qilganda — sonlar biroz o'zgardi:
 
```
"V" ko'p → sonlar "V" tomonga surildi
Oldin:  w[2847] =  0.234
Keyin:  w[2847] =  0.241  ← "V" ga qarab o'zgardi
```
 
### Bashoratda
 
```
O'qitishda "V" ko'p ko'rgan
→ sonlar "V" ga qarab sozlangan
→ bashoratda "V" → 89%, "VI" → 3%
→ "V" tanlandi ✅
```
 
### Muhim ogohlantirish — Hallucination
 
```
Model noto'g'ri ham bashorat qilishi mumkin:
 
Savol: "Samarqandda metro bormi?"
Javob: "Ha, 1985 yilda qurilgan" ← noto'g'ri! ❌
       (metro yo'q, lekin model "bashorat" qildi)
```
 
Model haqiqatni bilmaydi — faqat o'qitish ma'lumotidagi
**eng ko'p takrorlangan javobni** bashorat qiladi.
 
---
 
 
## 18. HuggingFace Transformers nima?
 
### HuggingFace nima?
 
HuggingFace = **AI modellari uchun GitHub**.
 
```
GitHub:
→ dasturchilar kod saqlaydi
→ bepul, ochiq
→ kimdir yozgan kodni yuklab ishlatasan
 
HuggingFace:
→ tadqiqotchilar AI modellarini saqlaydi
→ bepul, ochiq
→ kimdir o'qitgan modelni yuklab ishlatasan
```
 
---
 
## HuggingFace Transformers nima?
 
HuggingFace ning eng mashhur **Python kutubxonasi**.
 
```
pip install transformers
```
 
Bu kutubxona nima qiladi?
 
```
HuggingFace hub da → minglab model bor
Transformers kutubxonasi → shu modellarni
                           Python da ishlatishni
                           osonlashtiradi
```

---
 
## 19. Ollama nima?
 
LLM modellarni **lokal** ishga tushirish uchun qulay vosita.
 
```
Ollama = Django development server (manage.py runserver)
```
 
```
├── O'rnatish: 1 buyruq
├── GGUF format (siqilgan model) ishlatadi
├── 1 foydalanuvchi uchun ideal
├── CPU da ham yaxshi ishlaydi
└── Production uchun emas
```
 
```bash
ollama pull gemma3:1b   # yuklab olish
ollama run  gemma3:1b   # ishga tushirish
ollama list             # yuklangan modellar
```
 
---
 
## 20. vLLM nima?
 
**Production** uchun mo'ljallangan LLM server.
 
```
vLLM = Gunicorn + Nginx (production server)
```
 
```
├── PagedAttention ishlatadi       → VRAM samarali
├── Continuous batching            → ko'p foydalanuvchi bir vaqtda
├── OpenAI API bilan mos           → to'g'ridan-to'g'ri almashtirish
└── GPU talab qiladi
```
 
### Continuous batching nima?
 
```
Oddiy tizim (Ollama):
Foydalanuvchi 1: [========] tugaydi
Foydalanuvchi 2:            [========] boshlanadi
→ Navbat bilan ✅ lekin sekin
 
vLLM Continuous batching:
Foydalanuvchi 1: [====----]
Foydalanuvchi 2:     [====----]
Foydalanuvchi 3:         [====----]
→ Bir vaqtda, bo'sh joylarni to'ldiradi ✅
```
 
---
 
## 21. Gemma3 nima?
 
Google tomonidan yaratilgan **ochiq** LLM modeli.
 
```
Ochiq model  = kodi va og'irliklari barchaga bepul
Yopiq model  = ChatGPT, Claude (faqat API orqali)
```
 
```
gemma3:1b   → 1 milliard parametr  → kichik, tez, oddiy savollar
gemma3:4b   → 4 milliard parametr  → o'rta
gemma4:e4b  → ~8 milliard (MoE)    → katta, aqlli, lekin sekin
```
 
**Parametr** = modelning "bilim sig'imi".
Qancha ko'p → aqlli, lekin ko'p VRAM kerak.
 
---
 
## 22. Hammasi birgalikda — arxitektura
 
```
┌─────────────────────────────────────────────────┐
│  LLM (Gemma3, Llama, Mistral)                   │
│  └── Transformer arxitekturasi                  │
│       ├── Embedding (token → vektor)            │
│       ├── Attention (tokenlar bir-birini ko'radi)│
│       ├── 18 qatlam (ma'noni chuqurlashtiradi)  │
│       ├── KV Cache (qayta hisoblamamlik)         │
│       └── Bashorat (32,000 token → 1 tanlov)    │
└─────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────┐
│  Server                                         │
│  ├── Ollama  → oddiy, 1 foydalanuvchi, CPU ✅   │
│  └── vLLM   → tez, ko'p foydalanuvchi, GPU 🚀  │
│               └── PagedAttention               │
└─────────────────────────────────────────────────┘
                        ↕ HTTP
┌─────────────────────────────────────────────────┐
│  FastAPI                                        │
│  ├── POST /chat         → normal javob          │
│  └── POST /chat/stream  → token-by-token (SSE)  │
└─────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────┐
│  Hardware                                       │
│  ├── CPU  → Ollama (gemma4:e4b CPU da) 😐       │
│  └── GPU  → vLLM  (gemma3:1b GPU da) 🚀        │
│             └── CUDA (ko'prik)                  │
└─────────────────────────────────────────────────┘
```
 
---
 
## 23. Tushunchalar ketma-ketligi
 
```
Token           → matn bo'lagi
    ↓
Embedding       → token → 768 ta son (vektor)
    ↓
Matritsa        → vektorni boyitish (hisob-kitob)
    ↓
Attention       → tokenlar bir-birini ko'radi (Q, K, V)
    ↓
KV Cache        → qayta hisoblamamlik (tezlashtirish)
    ↓
Qatlam (Layer)  → Attention + Feed Forward (18 marta)
    ↓
Bashorat        → 32,000 token → Softmax → 1 tanlov
    ↓
LLM             → bu jarayonni bajaruvchi model
    ↓
Transformer     → LLM ning arxitekturasi (2017)
    ↓
HuggingFace     → Transformer ni Python da ishlatish
    ↓
Ollama          → LLM ni lokal ishga tushirish (dev)
    ↓
vLLM            → LLM ni tez ishga tushirish (prod)
    ↓
PagedAttention  → vLLM ning KV Cache yaxshilanishi
    ↓
CUDA            → Python va GPU o'rtasidagi ko'prik
    ↓
GPU             → parallel hisob-kitob (2048 yadro)
    ↓
CPU             → ketma-ket hisob-kitob (4-16 yadro)
    ↓
VRAM            → GPU xotirasi (bizda 4GB)
```
 
---

## 24. Amaliyotlar

 - [Step 1. Muhitni Sozlash](step-1.md)  
 - [Step 2. Ollama + Chat](step-2.md)
