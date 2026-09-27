"""Fixed texts the assistant shows: the disclaimer, abstention and scope messages, labels.

Keeping them here (not in prompts) guarantees they are always present, identical and
never altered by the LLM. Each entry has English, Hindi and Marathi. The Hindi and
Marathi wording should be reviewed by a native speaker before the demo.
"""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "disclaimer": {
        "en": "This is information, not legal advice.",
        "hi": "यह जानकारी है, कानूनी सलाह नहीं।",
        "mr": "ही माहिती आहे, कायदेशीर सल्ला नाही.",
    },
    "abstain_no_sources": {
        "en": "I couldn't find anything in the loaded documents for this jurisdiction that answers your "
        "question, so I won't guess. You can rephrase, or talk to an IP facilitator.",
        "hi": "मुझे इस क्षेत्राधिकार के लिए लोड किए गए दस्तावेज़ों में आपके प्रश्न का उत्तर देने वाली कोई जानकारी "
        "नहीं मिली, इसलिए मैं अनुमान नहीं लगाऊँगा। आप प्रश्न दूसरे शब्दों में पूछ सकते हैं या किसी IP सुविधाकर्ता से बात कर सकते हैं।",
        "mr": "या अधिकारक्षेत्रासाठी लोड केलेल्या दस्तऐवजांमध्ये तुमच्या प्रश्नाचे उत्तर देणारी माहिती मला सापडली नाही, "
        "म्हणून मी अंदाज लावणार नाही. तुम्ही प्रश्न वेगळ्या शब्दांत विचारू शकता किंवा IP सुविधाकर्त्याशी बोलू शकता.",
    },
    "abstain_insufficient": {
        "en": "The documents I retrieved don't clearly answer this question, so I won't guess. "
        "An IP facilitator can help you with it.",
        "hi": "मुझे मिले दस्तावेज़ इस प्रश्न का स्पष्ट उत्तर नहीं देते, इसलिए मैं अनुमान नहीं लगाऊँगा। "
        "कोई IP सुविधाकर्ता इसमें आपकी मदद कर सकता है।",
        "mr": "मला मिळालेले दस्तऐवज या प्रश्नाचे स्पष्ट उत्तर देत नाहीत, म्हणून मी अंदाज लावणार नाही. "
        "IP सुविधाकर्ता तुम्हाला यात मदत करू शकतो.",
    },
    "abstain_low_confidence": {
        "en": "I found some possibly related provisions, but I'm not confident enough that they answer your "
        "question. Please check the sources below or talk to an IP facilitator.",
        "hi": "मुझे कुछ संभावित रूप से संबंधित प्रावधान मिले, लेकिन मुझे पर्याप्त भरोसा नहीं है कि वे आपके प्रश्न का "
        "उत्तर देते हैं। कृपया नीचे दिए स्रोत देखें या किसी IP सुविधाकर्ता से बात करें।",
        "mr": "मला काही संभाव्य संबंधित तरतुदी सापडल्या, पण त्या तुमच्या प्रश्नाचे उत्तर देतात याची मला पुरेशी खात्री नाही. "
        "कृपया खालील स्रोत पाहा किंवा IP सुविधाकर्त्याशी बोला.",
    },
    "abstain_no_corpus": {
        "en": "No documents have been loaded for this jurisdiction yet, so I can't answer. "
        "(Administrators: add documents to data/raw/ and run the ingest script.)",
        "hi": "इस क्षेत्राधिकार के लिए अभी कोई दस्तावेज़ लोड नहीं किया गया है, इसलिए मैं उत्तर नहीं दे सकता। "
        "(प्रशासक: data/raw/ में दस्तावेज़ जोड़ें और ingest स्क्रिप्ट चलाएँ।)",
        "mr": "या अधिकारक्षेत्रासाठी अद्याप कोणतेही दस्तऐवज लोड केलेले नाहीत, म्हणून मी उत्तर देऊ शकत नाही. "
        "(प्रशासक: data/raw/ मध्ये दस्तऐवज जोडा आणि ingest स्क्रिप्ट चालवा.)",
    },
    "abstain_unsupported": {
        "en": "I drafted an answer, but my fact-check could not confirm it against the sources, so I've withheld "
        "it. Please check the related provisions below or talk to an IP facilitator.",
        "hi": "मैंने एक उत्तर तैयार किया, लेकिन मेरी तथ्य-जाँच उसे स्रोतों से पुष्ट नहीं कर सकी, इसलिए मैंने उसे रोक दिया है। "
        "कृपया नीचे संबंधित प्रावधान देखें या किसी IP सुविधाकर्ता से बात करें।",
        "mr": "मी एक उत्तर तयार केले, पण माझ्या तथ्य-तपासणीत ते स्रोतांशी जुळले नाही, म्हणून मी ते रोखले आहे. "
        "कृपया खालील संबंधित तरतुदी पाहा किंवा IP सुविधाकर्त्याशी बोला.",
    },
    "possibly_related": {
        "en": "Possibly related provisions you can read:",
        "hi": "संभावित रूप से संबंधित प्रावधान जिन्हें आप पढ़ सकते हैं:",
        "mr": "तुम्ही वाचू शकता अशा संभाव्य संबंधित तरतुदी:",
    },
    "escalation_recorded": {
        "en": "Your request for an IP facilitator has been recorded (reference {reference}). Quote this reference "
        "when you contact the IP facilitation desk. Please don't share personal details in this chat.",
        "hi": "IP सुविधाकर्ता के लिए आपका अनुरोध दर्ज कर लिया गया है (संदर्भ {reference})। IP सुविधा डेस्क से संपर्क "
        "करते समय यह संदर्भ बताएँ। कृपया इस चैट में व्यक्तिगत जानकारी साझा न करें।",
        "mr": "IP सुविधाकर्त्यासाठी तुमची विनंती नोंदवली गेली आहे (संदर्भ {reference}). IP सुविधा डेस्कशी संपर्क "
        "साधताना हा संदर्भ सांगा. कृपया या चॅटमध्ये वैयक्तिक माहिती शेअर करू नका.",
    },
    "out_of_scope_medical": {
        "en": "I can't help with medical, dosage or treatment questions — please consult a qualified Ayurveda "
        "practitioner. I can answer questions about intellectual property and regulatory rules for Ayurvedic products.",
        "hi": "मैं चिकित्सा, खुराक या उपचार संबंधी प्रश्नों में मदद नहीं कर सकता — कृपया किसी योग्य आयुर्वेद चिकित्सक से "
        "परामर्श करें। मैं आयुर्वेदिक उत्पादों के बौद्धिक संपदा और नियामक नियमों से जुड़े प्रश्नों के उत्तर दे सकता हूँ।",
        "mr": "मी वैद्यकीय, मात्रा किंवा उपचारविषयक प्रश्नांमध्ये मदत करू शकत नाही — कृपया पात्र आयुर्वेद वैद्यांचा सल्ला "
        "घ्या. मी आयुर्वेदिक उत्पादनांच्या बौद्धिक संपदा आणि नियामक नियमांविषयीच्या प्रश्नांची उत्तरे देऊ शकतो.",
    },
    "off_topic": {
        "en": "That's outside what I can help with. I answer questions about intellectual property (patents, trade "
        "marks, GI, designs, copyright, plant varieties), access and benefit sharing, traditional knowledge, and "
        "regulatory approvals for Ayurvedic products.",
        "hi": "यह मेरे दायरे से बाहर है। मैं बौद्धिक संपदा (पेटेंट, ट्रेडमार्क, GI, डिज़ाइन, कॉपीराइट, पौध किस्में), "
        "पहुँच और लाभ-साझाकरण, पारंपरिक ज्ञान और आयुर्वेदिक उत्पादों की नियामक स्वीकृतियों से जुड़े प्रश्नों के उत्तर देता हूँ।",
        "mr": "हे माझ्या कार्यक्षेत्राबाहेर आहे. मी बौद्धिक संपदा (पेटंट, ट्रेडमार्क, GI, डिझाइन, कॉपीराइट, वनस्पती वाण), "
        "प्रवेश व लाभ-वाटप, पारंपरिक ज्ञान आणि आयुर्वेदिक उत्पादनांच्या नियामक मंजुरींविषयीच्या प्रश्नांची उत्तरे देतो.",
    },
    "greeting": {
        "en": "Namaste! I explain intellectual-property and regulatory rules for Ayurvedic products, citing the exact "
        "provision each answer comes from. Try one of these, or ask your own question:",
        "hi": "नमस्ते! मैं आयुर्वेदिक उत्पादों के बौद्धिक संपदा और नियामक नियम समझाता हूँ और हर उत्तर का सटीक स्रोत-प्रावधान "
        "बताता हूँ। इनमें से कोई प्रश्न चुनें या अपना प्रश्न पूछें:",
        "mr": "नमस्कार! मी आयुर्वेदिक उत्पादनांचे बौद्धिक संपदा आणि नियामक नियम समजावून सांगतो आणि प्रत्येक उत्तराची नेमकी "
        "स्रोत-तरतूद सांगतो. यापैकी एखादा प्रश्न निवडा किंवा तुमचा प्रश्न विचारा:",
    },
    "legal_advice_notice": {
        "en": "I can't advise on your specific situation or dispute. Below is general information from the sources; "
        "for your case, please talk to an IP facilitator.",
        "hi": "मैं आपकी विशिष्ट स्थिति या विवाद पर सलाह नहीं दे सकता। नीचे स्रोतों से सामान्य जानकारी दी गई है; "
        "अपने मामले के लिए कृपया किसी IP सुविधाकर्ता से बात करें।",
        "mr": "मी तुमच्या विशिष्ट परिस्थितीवर किंवा वादावर सल्ला देऊ शकत नाही. खाली स्रोतांमधील सामान्य माहिती दिली आहे; "
        "तुमच्या प्रकरणासाठी कृपया IP सुविधाकर्त्याशी बोला.",
    },
    "flow_intro": {
        "en": "Let's work out your product's regulatory category. I'll ask a few quick questions.",
        "hi": "आइए आपके उत्पाद की नियामक श्रेणी पता करें। मैं कुछ छोटे प्रश्न पूछूँगा।",
        "mr": "चला, तुमच्या उत्पादनाची नियामक श्रेणी ठरवूया. मी काही छोटे प्रश्न विचारेन.",
    },
    "flow_cancelled": {
        "en": "Okay, I've stopped the product classification. Ask me anything else.",
        "hi": "ठीक है, मैंने उत्पाद वर्गीकरण रोक दिया है। कुछ और पूछिए।",
        "mr": "ठीक आहे, मी उत्पादन वर्गीकरण थांबवले आहे. आणखी काहीही विचारा.",
    },
    "partial_answer": {
        "en": "I couldn't answer the part about {topics} from the loaded sources.",
        "hi": "लोड किए गए स्रोतों से मैं {topics} वाले हिस्से का उत्तर नहीं दे सका।",
        "mr": "लोड केलेल्या स्रोतांमधून मी {topics} या भागाचे उत्तर देऊ शकलो नाही.",
    },
    "links_heading": {
        "en": "Official portals (team-verified list):",
        "hi": "आधिकारिक पोर्टल (टीम द्वारा सत्यापित सूची):",
        "mr": "अधिकृत पोर्टल (टीमने पडताळलेली यादी):",
    },
    "links_not_verified": {
        "en": "_Official portal links for this topic haven't been verified by the team yet._",
        "hi": "_इस विषय के आधिकारिक पोर्टल लिंक अभी टीम द्वारा सत्यापित नहीं किए गए हैं।_",
        "mr": "_या विषयाचे अधिकृत पोर्टल दुवे अद्याप टीमने पडताळलेले नाहीत._",
    },
    "translation_unavailable": {
        "en": "Translation is unavailable right now, so this answer is shown in English.",
        "hi": "अनुवाद अभी उपलब्ध नहीं है, इसलिए यह उत्तर अंग्रेज़ी में दिखाया गया है।",
        "mr": "भाषांतर सध्या उपलब्ध नाही, म्हणून हे उत्तर इंग्रजीत दाखवले आहे.",
    },
    "extractive_intro": {
        "en": "The AI writer is unavailable right now, so here are the most relevant provisions, quoted from the "
        "sources:",
        "hi": "AI लेखक अभी उपलब्ध नहीं है, इसलिए स्रोतों से उद्धृत सबसे प्रासंगिक प्रावधान यहाँ दिए गए हैं:",
        "mr": "AI लेखक सध्या उपलब्ध नाही, म्हणून स्रोतांमधून उद्धृत केलेल्या सर्वात संबंधित तरतुदी येथे आहेत:",
    },
    # Specialist section titles
    "agent_formulation_classification": {"en": "Product category", "hi": "उत्पाद श्रेणी", "mr": "उत्पादन श्रेणी"},
    "agent_ip_protection": {"en": "Intellectual property", "hi": "बौद्धिक संपदा", "mr": "बौद्धिक संपदा"},
    "agent_abs_compliance": {"en": "Access & benefit sharing", "hi": "पहुँच और लाभ-साझाकरण", "mr": "प्रवेश व लाभ-वाटप"},
    "agent_prior_art_tk": {
        "en": "Traditional knowledge & prior art",
        "hi": "पारंपरिक ज्ञान और पूर्व कला",
        "mr": "पारंपरिक ज्ञान आणि पूर्वकला",
    },
    "agent_registry_navigation": {"en": "Where to apply", "hi": "कहाँ आवेदन करें", "mr": "कुठे अर्ज करावा"},
    "agent_general_regulatory": {"en": "Regulatory information", "hi": "नियामक जानकारी", "mr": "नियामक माहिती"},
    # Starter prompts (greeting quick replies)
    "starter_patent": {
        "en": "Can I patent a classical Ayurvedic formulation?",
        "hi": "क्या मैं किसी शास्त्रीय आयुर्वेदिक योग का पेटेंट करा सकता हूँ?",
        "mr": "मी एखाद्या शास्त्रीय आयुर्वेदिक योगाचे पेटंट घेऊ शकतो का?",
    },
    "starter_plant": {
        "en": "What approvals do I need to use a medicinal plant commercially?",
        "hi": "किसी औषधीय पौधे का व्यावसायिक उपयोग करने के लिए मुझे कौन-सी स्वीकृतियाँ चाहिए?",
        "mr": "औषधी वनस्पतीचा व्यावसायिक वापर करण्यासाठी मला कोणत्या मंजुऱ्या लागतील?",
    },
    "starter_classify": {
        "en": "Which regulatory category does my herbal product fall into?",
        "hi": "मेरा हर्बल उत्पाद किस नियामक श्रेणी में आता है?",
        "mr": "माझे हर्बल उत्पादन कोणत्या नियामक श्रेणीत येते?",
    },
}


def msg(key: str, language: str = "en") -> str:
    """Look up a fixed message, falling back to English."""
    entry = MESSAGES[key]
    return entry.get(language) or entry["en"]
