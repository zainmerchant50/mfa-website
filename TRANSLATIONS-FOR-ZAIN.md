# Hindi and Urdu wording for /hindi-urdu-accountant/ (DRAFT, needs Zain's review)

Branch `hindi-urdu-page`. Every non-English string on the page is listed below with its English meaning.
Source: `tools/build_hindi_urdu.py` (`HI`, `UR`, `FAQ_HI`, `FAQ_UR`, and the two FAQ box labels in `build()`).
Edit the strings there, then run `python3 tools/build_resources.py`.

Hindi uses `lang="hi"` (Noto Sans Devanagari). Urdu uses `lang="ur" dir="rtl"` (Noto Nastaliq Urdu). Dollar amounts inside Urdu text are wrapped in `<span dir="ltr">` so "$199" doesn't flip to "199$".

## Hero, Hindi box

| # | Hindi | English meaning |
|---|---|---|
| H1 | हिंदी | Hindi (box label) |
| H2 | एडिसन, आइसलिन और सेंट्रल न्यू जर्सी में हिंदी और उर्दू बोलने वाले अकाउंटेंट और टैक्स प्रिपेयरर | Hindi and Urdu speaking accountant and tax preparer in Edison, Iselin and Central New Jersey |
| H3 | आपके बिज़नेस और परिवार के लिए बुककीपिंग, टैक्स रिटर्न, 1099 और LLC सेटअप। | Bookkeeping, tax returns, 1099s and LLC setup for your business and family. |
| H4 | हमसे हिंदी, उर्दू या अंग्रेज़ी में बात करें। | Talk to us in Hindi, Urdu or English. |
| H5 | काम शुरू होने से पहले साफ़ कीमत बताई जाती है। | You're told a clear price before the work starts. |
| H6 | कॉल बुक करें → | Book a call → (links to /book/) |

## Hero, Urdu box

| # | Urdu | English meaning |
|---|---|---|
| U1 | اردو | Urdu (box label) |
| U2 | ایڈیسن، آئسلن اور سینٹرل نیو جرسی میں ہندی اور اردو بولنے والے اکاؤنٹنٹ اور ٹیکس پریپیئرر | Hindi and Urdu speaking accountant and tax preparer in Edison, Iselin and Central New Jersey |
| U3 | آپ کے کاروبار اور فیملی کے لیے بک کیپنگ، ٹیکس ریٹرن، 1099 اور LLC سیٹ اپ۔ | Bookkeeping, tax returns, 1099s and LLC setup for your business and family. |
| U4 | ہم سے اردو، ہندی یا انگریزی میں بات کریں۔ | Talk to us in Urdu, Hindi or English. |
| U5 | کام شروع ہونے سے پہلے صاف قیمت بتائی جاتی ہے۔ | You're told a clear price before the work starts. |
| U6 | کال بک کریں ← | Book a call ← (links to /book/; the arrow points left for right-to-left reading) |

## FAQ, short Hindi versions (of English FAQ 1 and 2)

| # | Hindi | English meaning |
|---|---|---|
| H7 | हिंदी में | In Hindi (box label) |
| H8 | क्या हम हिंदी या उर्दू में बात कर सकते हैं? | Can we talk in Hindi or Urdu? |
| H9 | हाँ। Google Meet या फ़ोन पर, हिंदी, उर्दू या अंग्रेज़ी में। टैक्स फ़ॉर्म अंग्रेज़ी में होते हैं, पर हम आपको हर चीज़ आपकी भाषा में समझाते हैं। | Yes. On Google Meet or by phone, in Hindi, Urdu or English. Tax forms are in English, but we explain everything to you in your language. |
| H10 | आपकी फ़ीस कितनी है? | How much is your fee? |
| H11 | मंथली बुककीपिंग $199 प्रति माह से शुरू होती है। टैक्स रिटर्न की कीमत काम शुरू होने से पहले बता दी जाती है। | Monthly bookkeeping starts from $199 a month. The price of a tax return is told to you before the work starts. |

## FAQ, short Urdu versions (of English FAQ 1 and 2)

| # | Urdu | English meaning |
|---|---|---|
| U7 | اردو میں | In Urdu (box label) |
| U8 | کیا ہم اردو یا ہندی میں بات کر سکتے ہیں؟ | Can we talk in Urdu or Hindi? |
| U9 | جی ہاں۔ Google Meet یا فون پر، اردو، ہندی یا انگریزی میں۔ ٹیکس فارم انگریزی میں ہوتے ہیں، لیکن ہم آپ کو ہر چیز آپ کی زبان میں سمجھاتے ہیں۔ | Yes. On Google Meet or by phone, in Urdu, Hindi or English. Tax forms are in English, but we explain everything to you in your language. |
| U10 | آپ کی فیس کتنی ہے؟ | How much is your fee? |
| U11 | ماہانہ بک کیپنگ $199 فی مہینہ سے شروع ہوتی ہے۔ ٹیکس ریٹرن کی قیمت کام شروع ہونے سے پہلے بتا دی جاتی ہے۔ | Monthly bookkeeping starts from $199 a month. The price of a tax return is told to you before the work starts. |

## Wording choices to check

- English loanwords kept on purpose because people say them that way: बिज़नेस (Hindi only; the Urdu uses کاروبار), बुककीपिंग / بک کیپنگ, टैक्स रिटर्न / ٹیکس ریٹرن, अकाउंटेंट / اکاؤنٹنٹ, टैक्स प्रिपेयरर / ٹیکس پریپیئرر, सेटअप / سیٹ اپ, फ़ीस / فیس. Urdu uses کاروبار (business) and فیملی (family); swap فیملی for خاندان if you prefer more formal Urdu.
- H11 and U11 say "monthly ... per month" (मंथली ... प्रति माह / ماہانہ ... فی مہینہ). Natural in speech, but you could drop one.
- Place names: आइसलिन / آئسلن for Iselin (EYE-zlin). Check this matches how the community says it.
- Brand and product names stay in English: Google Meet, LLC, 1099.

## Claims on the English part of the page that are new to the site (need your yes)

The page reuses the approved `?s=hindi-urdu` landing variant ("explained in English, Hindi or Urdu, with a clear quote upfront") and only existing public prices ($199/mo bookkeeping, $25 per 1099 with $75 minimum, LLC from $150 plus state fee; tax returns and sales tax filing "quoted up front"). These lines were not on the site before and came from the brief:

1. "US CPA candidate" (Why us and FAQ 4). Paired with "When an engagement needs a licensed CPA, we work with partner CPAs."
2. "Registered with the IRS as a paid tax preparer (PTIN) and as an authorized e-file provider (EFIN)."
3. "Founder Zain Merchant worked at PwC in New York on audits and internal controls before starting MFA."
4. "Sales tax filing: New Jersey sales and use tax returns filed on schedule" (no price shown).
5. The mfa-contentcreator skill still says "Don't mention languages on the site (Hindi/Urdu appears only in the Hindi-Urdu ad variant headline)". This page is the approved exception (2026-10-23); update that skill line when you merge.
