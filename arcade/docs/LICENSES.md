# سجل التراخيص والمدقق — شرط «من غير انتهاك» مُهندَساً

هذه الطبقة هي الفرق بين «أركيد يبيع» و«أركيد يبيع بأمان قانوني»: لا تظهر لعبة للزوار
ولا تُصدَّر في الحزمة الساكنة إلا إذا كان في السجل صف إثبات يناجح المدقق.

## المحرّكان، عقد واحد

| المحرك | الملف | أين يعمل |
|---|---|---|
| PHP | `src/License/LicenseAuditor.php` | الموقع الديناميكي + `bin/arcade.php licenses:audit` |
| Python | `tools/audit_ledger.py` | التصدير الساكن + بوابات CI |

**`tools/check_audit_parity.py` يفشل البناء فوراً** إذا اختلف المحرّكان في القواعد
المشتركة أو قائمتي المسموح/الممنوع — أُثبت عدم فراغه بحقن قاعدة وهمية فالتقطها.

## القواعد المشتركة (12)

`slug` · `no_license_row` · `license_type` · `license_status` · `license_expiry` ·
`copyleft` · `allow_list` · `proof_upstream` · `pin` · `external_id` · `runtime` · `attribution`

- **error** = تخفي اللعبة عن الزوار وتفشل البوابة. **warning** (مثل attribution الناقص)
  يمر عادياً ويفشل مع `--strict` فقط — مخصص لبوابات الإصدار.
- PHP فقط: `license_drift` (بصمة ملف الترخيص تغيّرت upstream) · `invoice` (اتفاق ناشر
  بلا فاتورة) · `local_path` (لعبة own بلا ملفات) · `provider_gate` (مزوّد غير مفعّل).
- Static فقط: `provider_unknown` · `expiry_format`.

## القائمتان

- **مسموح**: MIT · Apache-2.0 · BSD-2/3-Clause · ISC · 0BSD · Unlicense · Zlib ·
  OFL-1.1 · CC0-1.0 · + النوعان غير SPDX: `publisher-agreement` و`own-licence`.
- **ممنوع أي شيء يبدأ بـ**: `GPL` · `AGPL` · `LGPL` · `CC-BY-NC` · `BSD-4` · `NPOSL` · `SSPL`.

## شكل صف الإثبات (`game_licenses`)

نوع الترخيص (`oss` | `publisher-agreement` | `own`) يحدد المطلوب:

- `oss` → `upstream_repo` + `proof_url` + **commit_sha بصمة 40-hex كاملة** + مرجع مسموح.
- `publisher-agreement` → `invoice_ref` (الفاتورة) + `allow_origins` (النطاقات التي
  يغطيها العقد) + تاريخ انتهاء صالح.
- `own` → `local_path` موجود فعلاً على القرص (لعبتك، ملكك).

## التشغيل

```bash
php bin/arcade.php licenses:audit --strict        # للمشتري، على تثبيته
python3 tools/audit_ledger.py data/ledger.example.json   # جهة التصدير
python3 tools/prove_audit.py                      # 20 فحصاً بعدائية (حقن مخالفات)
```

سلوك الإخفاء مثبت ومطبق في `/api/games`: اللعبة غير الناجحة **لا تعبر الحد أبداً** —
في العرض الحي شاهد «مقاتل الظل» (GPL-3.0) مخفية تلقائياً بينما تمر الألعاب النظيفة.
