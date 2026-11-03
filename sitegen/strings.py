"""Every piece of visible text on the site and in the images, translated per locale."""

TEXT = {
    "en-US": {
        "role": "Customer Success Lead",
        "contact_label": "Contact",
        "banner_headline": "Meet your account manager",
        "quote": "“We answer every message within one business day.”",
        "signature_tagline": "Best Company · Customer Success",
        "product_captions": ["Best Company Cloud", "Analytics Suite", "Mobile App"],
        "alt_person": "Team member",
        "alt_product": "Product illustration",
        "footer_copyright": "© 2026 Best Company. Fictional demo site.",
        "language_label": "Language",
    },
    "ja-JP": {
        "role": "カスタマーサクセス担当",
        "contact_label": "連絡先",
        "banner_headline": "担当者のご紹介",
        "quote": "「すべてのお問い合わせに1営業日以内にお返事します。」",
        "signature_tagline": "Best Company・カスタマーサクセス",
        "product_captions": ["Best Company クラウド", "分析スイート", "モバイルアプリ"],
        "alt_person": "チームメンバー",
        "alt_product": "製品イメージ",
        "footer_copyright": "© 2026 Best Company。架空のデモサイトです。",
        "language_label": "言語",
    },
    "ar-SA": {
        # Wording avoids grammatical gender, since the persona's gender is not specified.
        "role": "فريق نجاح العملاء",
        "contact_label": "للتواصل",
        "banner_headline": "تعرّف على مدير حسابك",
        # Plain quotes: guillemets get mirrored in right-to-left text and look reversed.
        "quote": '"نرد على كل رسالة خلال يوم عمل واحد."',
        "signature_tagline": "Best Company · نجاح العملاء",
        "product_captions": ["سحابة Best Company", "حزمة التحليلات", "تطبيق الجوال"],
        "alt_person": "عضو في الفريق",
        "alt_product": "صورة توضيحية للمنتج",
        "footer_copyright": "© 2026 Best Company. موقع تجريبي خيالي.",
        "language_label": "اللغة",
    },
}

# Page titles. The first five are in the main menu and in sitemap.xml.
# "legacy-team" and "press-archive" are hidden pages linked only from the footer.
PAGE_TITLES = {
    "en-US": {"index": "Home", "about": "About us", "team": "Our team", "news": "News",
              "contact": "Contact", "legacy-team": "Team (2023 archive)",
              "press-archive": "Press archive"},
    "ja-JP": {"index": "ホーム", "about": "会社概要", "team": "チーム紹介", "news": "お知らせ",
              "contact": "お問い合わせ", "legacy-team": "チーム（2023年アーカイブ）",
              "press-archive": "プレスアーカイブ"},
    "ar-SA": {"index": "الرئيسية", "about": "من نحن", "team": "فريقنا", "news": "الأخبار",
              "contact": "اتصل بنا", "legacy-team": "الفريق (أرشيف 2023)",
              "press-archive": "أرشيف الصحافة"},
}

LANGUAGE_NAMES = {"en-US": "English", "ja-JP": "日本語", "ar-SA": "العربية"}
