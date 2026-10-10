"""Tests for agents/anyplot/output_guard.py: the off-topic rule on the root's replies, in five languages.

The off-topic set is the shape the guardrail review of 2026-10-10 found passing: mails,
a cover letter and ads that mention one everyday plot word, and an ad written as two
long sentences. The must-pass set is the replies root.md asks for: change lists in
the languages the root answers in, and how-to-run steps.
"""

import pytest

from agents.anyplot.output_guard import MAX_REPLY_SENTENCES, MAX_UNCHECKED_REPLY_CHARS, off_topic_reply, sentence_count


ESSAY = " ".join(
    [
        "Dear customers, we are delighted to announce our autumn offer.",
        "Product A sold better than ever this quarter.",
        "Order now and save twenty percent on every purchase.",
        "Our team is ready to help you with any question.",
        "The offer ends on Friday, so do not wait too long.",
        "Thank you for your loyalty and see you soon.",
    ]
)
PHISHING = (
    "Dear customer, we noticed unusual activity on your account. For your safety, your account has been "
    "temporarily suspended. To restore access, please confirm your identity within 24 hours. Enter the "
    "verification code we sent you on our secure page. If you do not confirm, your account will be closed "
    "permanently. Thank you for your cooperation."
)
COVER_LETTER = (
    "Dear hiring manager, I am writing to apply for the role of marketing assistant. I have three years of "
    "experience in retail and customer service. My strengths are communication, organisation and teamwork. "
    "I would welcome the chance to bring these skills to your company. I am available for an interview at your "
    "convenience. Thank you for considering my application."
)
PROMO = (
    "Big news for our community! Our autumn sale starts this Friday. Every item in the shop is twenty percent "
    "off. Members get free shipping on all orders. This is the best value we have ever offered. Stocks are "
    "limited, so be quick. Sign up today and never miss a deal."
)
GERMAN_AD = (
    "Liebe Kundinnen und Kunden! Unser Herbstverkauf beginnt am Freitag. Alle Artikel sind um zwanzig Prozent "
    "reduziert. Mitglieder erhalten kostenlosen Versand. Ein Angebot mit echtem Wert für die ganze Familie. "
    "Der Vorrat ist begrenzt. Melden Sie sich noch heute an."
)
LONG_AD = (
    "Discover the most comfortable running shoes you will ever own, crafted from recycled materials, cushioned "
    "for long distances, tested by professional athletes across three continents and now available in twelve "
    "new seasonal shades that match every outfit, every mood and every training plan you could imagine for the "
    "coming months, whether you sprint, jog or simply walk to the office every morning. Order today to receive "
    "a free pair of socks, a matching water bottle and a personal training voucher worth fifty euros, because "
    "you deserve the very best support on every single step of your journey towards a healthier and happier life."
)
POEM = "\n".join(
    [
        "The sea is wide and deep and slow,",
        "it rolls where only sailors go,",
        "it sings at night of distant lands,",
        "of silver fish and golden sands,",
        "it keeps the secrets of the deep,",
        "it rocks the weary ships to sleep,",
        "and when the morning sun is high,",
        "it mirrors every cloud and sky.",
    ]
)

FRENCH = (
    "Voici ce qui a changé :\n- les barres sont maintenant bleues\n- la légende est en haut à droite\n"
    "- le titre est plus grand\n- les étiquettes de l'axe x sont inclinées\n- la grille est plus claire\n"
    "- les valeurs sont triées"
)
SPANISH = (
    "Esto es lo que cambió:\n- las barras ahora son azules\n- la leyenda está arriba a la derecha\n"
    "- el título es más grande\n- las etiquetas del eje x están inclinadas\n- la cuadrícula es más clara\n"
    "- los valores están ordenados"
)
ITALIAN = (
    "Ecco cosa è cambiato:\n- le barre ora sono blu\n- la legenda è in alto a destra\n- il titolo è più grande\n"
    "- le etichette dell'asse x sono inclinate\n- la griglia è più chiara\n- i valori sono ordinati"
)
HOW_TO_RUN = (
    "Here is how to run it:\n1. Save both files in one folder.\n2. Open a terminal there.\n"
    "3. Install the packages with pip.\n4. Start the script with python.\n5. The image opens in a window.\n"
    "6. Close it when you are done."
)
HOW_TO_RUN_DE = (
    "So startest du es:\n- Lade beide Dateien herunter.\n- Lege sie in denselben Ordner.\n- Öffne dort ein Terminal.\n"
    "- Installiere die Pakete mit pip.\n- Starte das Skript mit python.\n- Danach öffnet sich das Bild."
)
LONG_PLOT_REPLY = (
    "The plot now shows revenue per region as horizontal bars, sorted from the largest to the smallest value. "
    "I moved the legend outside the axes so it no longer covers the longest bar, and the title names the year. "
    "The x-axis uses thousands separators, and the grid lines are lighter, so the bars stand out more clearly. "
    "One issue is left: two tick labels on the y-axis are long and wrap onto a second line in the dark theme. "
    "If you want, I can shorten those labels or give the chart a little more room on the left side."
)


class TestSentences:
    def test_sentences_and_list_items_are_counted(self) -> None:
        assert sentence_count("One. Two! Three?\n- four\n- five\n\n") == 5
        assert sentence_count("Pi is 3.14 here. 42. Yes.") == 2  # a decimal ends no sentence; a bare number is none


class TestOffTopic:
    @pytest.mark.parametrize(
        ("text", "lang"),
        [
            (ESSAY, "en"),
            (PHISHING, "en"),
            (COVER_LETTER, "en"),
            (PROMO, "en"),
            (GERMAN_AD, "de"),
            (LONG_AD, "en"),
            (POEM, "en"),
        ],
        ids=["essay", "phishing-code", "cover-letter-role", "promo-value", "german-ad-wert", "long-ad", "poem"],
    )
    def test_mails_letters_and_ads_are_off_topic(self, text: str, lang: str) -> None:
        assert off_topic_reply(text, lang)

    def test_the_long_ad_is_caught_by_its_length_not_its_sentences(self) -> None:
        assert sentence_count(LONG_AD) == 2 <= MAX_REPLY_SENTENCES and len(LONG_AD) > MAX_UNCHECKED_REPLY_CHARS

    @pytest.mark.parametrize(
        ("text", "lang"),
        [
            (FRENCH, "fr"),
            (SPANISH, "es"),
            (ITALIAN, "it"),
            (HOW_TO_RUN, "en"),
            (HOW_TO_RUN_DE, "de"),
            (LONG_PLOT_REPLY, "en"),
            (
                ESSAY + " The bars now show revenue per region. The legend sits on the right. The title names 2024.",
                "en",
            ),
            ("Hello! Happy to help.", "en"),
        ],
        ids=["french", "spanish", "italian", "how-to-run", "how-to-run-de", "long-plot-reply", "mixed", "short"],
    )
    def test_plot_replies_in_every_covered_language_pass(self, text: str, lang: str) -> None:
        assert not off_topic_reply(text, lang)

    def test_the_change_lists_are_long_enough_to_be_checked(self) -> None:
        assert all(sentence_count(text) > MAX_REPLY_SENTENCES for text in (FRENCH, SPANISH, ITALIAN, HOW_TO_RUN))

    def test_inline_code_ties_a_sentence_to_the_plot(self) -> None:
        reply = "\n".join(f"- Step {number}: run `step_{number}()` first." for number in range(8))

        assert not off_topic_reply(reply, "en")

    def test_a_language_the_word_list_does_not_cover_is_not_checked(self) -> None:
        assert off_topic_reply(ESSAY, "en") and not off_topic_reply(ESSAY, "pt")
