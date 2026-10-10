"""Tests for agents/anyplot/output_guard.py: the reply cap on the root's replies, the same in every language.

The must-pass set is the replies root.md asks for ("two to five sentences, or a short
list"): change lists and how-to-run steps in the languages the root answers in, a
long five-sentence reply in German, and replies in scripts without spaces between
sentences. The must-refuse set is text no reply of root.md's shape reaches: a long
customer mail, a long Japanese essay and a list of sixty items.
"""

import pytest

from agents.anyplot.output_guard import MAX_MESSAGE_CHARS, reply_length, reply_too_long, sanitize


CUSTOMER_MAIL = " ".join(
    [
        "Dear customers, we are delighted to announce our big autumn offer, and we want you to be the first to know.",
        "Product A sold better than ever this quarter, and we have decided to share that success with all of you.",
        "From Friday on, every item in our shop is twenty percent off, and members get free shipping on every order.",
        "Order now and save on every purchase, because stocks are limited and the best sizes always go first.",
        "Our friendly team is ready to help you with any question about sizes, delivery times or returns.",
        "If you have not signed up for our newsletter yet, now is the perfect moment to do so and never miss a deal.",
        "Members also receive a personal birthday voucher and early access to every seasonal collection we launch.",
        "The offer ends on Friday at midnight, so please do not wait too long if you have your eye on something.",
        "Tell your friends and family about it too, because every new member also gets a welcome gift on sign-up.",
        "Thank you for your loyalty over all these years, and we look forward to seeing you again very soon.",
        "Warm regards from all of us, and enjoy the most colourful season of the year with your loved ones.",
        "P.S. Our stores in every city stay open until ten in the evening on Friday and Saturday this week.",
        "P.P.S. Follow us on social media for daily deals, styling tips and stories from the people behind our brand.",
    ]
)
JAPANESE_ESSAY = "海はとても広くて深く、遠い国の物語を静かに語り続けている。" * 45
SIXTY_ITEMS = "\n".join(f"- Item {number}: order today and get a free gift with every purchase" for number in range(60))

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
PORTUGUESE_STEPS = (
    "Para executar o gráfico no seu computador:\n1. Instale o Python 3.12 ou mais recente.\n"
    "2. Instale os pacotes com pip install matplotlib pandas.\n3. Baixe o plot.py e o data.csv.\n"
    "4. Coloque os dois arquivos na mesma pasta.\n5. Abra um terminal nessa pasta.\n"
    "6. Execute python plot.py.\n7. A imagem é salva como plot-light.png.\n8. Abra a imagem para conferir o resultado."
)
POLISH = (
    "Wykres jest gotowy. Słupki pokazują sprzedaż w każdym regionie, posortowaną od największej. "
    "Legenda jest teraz po prawej stronie, a tytuł podaje rok."
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
LONG_PLOT_REPLY_DE = (
    "Der Plot zeigt jetzt den Umsatz pro Region als waagerechte Balken, absteigend nach dem größten Wert sortiert. "
    "Die Legende habe ich außerhalb der Achsen platziert, damit sie den längsten Balken nicht mehr verdeckt, und der "
    "Titel nennt jetzt das Geschäftsjahr. Die x-Achse verwendet Tausendertrennzeichen, und die Gitterlinien sind "
    "heller, sodass sich die Balken deutlicher vom Hintergrund abheben. Ein Problem bleibt: Zwei Beschriftungen auf "
    "der y-Achse sind sehr lang und brechen im dunklen Design auf eine zweite Zeile um. Wenn du möchtest, kann ich "
    "diese Beschriftungen kürzen oder dem Diagramm auf der linken Seite etwas mehr Platz geben."
)
JAPANESE = "プロットができました。棒は売上の大きい順に並んでいます。凡例は右上にあります。タイトルには年を入れました。"
CHINESE = "图表已经完成。柱子按销售额从高到低排列，图例在右上角，标题写明了年份。需要的话，我可以把颜色改成蓝色。"


class TestReplyCap:
    @pytest.mark.parametrize(
        "text", [CUSTOMER_MAIL, JAPANESE_ESSAY, SIXTY_ITEMS], ids=["customer-mail", "japanese-essay", "sixty-items"]
    )
    def test_text_longer_than_any_reply_is_refused(self, text: str) -> None:
        assert reply_length(text) > MAX_MESSAGE_CHARS and reply_too_long(text)

    @pytest.mark.parametrize(
        "text",
        [
            FRENCH,
            SPANISH,
            ITALIAN,
            PORTUGUESE_STEPS,
            POLISH,
            HOW_TO_RUN,
            HOW_TO_RUN_DE,
            LONG_PLOT_REPLY,
            LONG_PLOT_REPLY_DE,
            JAPANESE,
            CHINESE,
            "Hello! Happy to help.",
        ],
        ids=[
            "french",
            "spanish",
            "italian",
            "portuguese-eight-steps",
            "polish",
            "how-to-run",
            "how-to-run-de",
            "five-long-sentences",
            "five-long-sentences-de",
            "japanese",
            "chinese",
            "short",
        ],
    )
    def test_replies_of_root_mds_shape_pass_in_every_language(self, text: str) -> None:
        assert not reply_too_long(text)

    def test_the_cap_is_counted_in_characters_whatever_the_script(self) -> None:
        for character in ("a", "é", "語", "ש"):
            assert not reply_too_long(character * MAX_MESSAGE_CHARS)
            assert reply_too_long(character * (MAX_MESSAGE_CHARS + 1))

    def test_the_cap_reads_the_sanitised_reply(self) -> None:
        code = "```python\n" + "\n".join(f"value_{number} = {number} * 1000" for number in range(60)) + "\n```"
        html = "<b>" * 500 + "The bars are blue."

        assert len(code) > MAX_MESSAGE_CHARS and not reply_too_long("Here is the code:\n" + code)
        assert len(html) > MAX_MESSAGE_CHARS and reply_length(html) == len("The bars are blue.")

    def test_the_cap_does_not_judge_content(self) -> None:
        """A short off-topic reply is the scope judge's to stop; the cap only bounds the length."""
        assert not reply_too_long("Our autumn sale starts on Friday. Every item is twenty percent off. Order now!")

    def test_the_sanitiser_still_cuts_at_the_cap(self) -> None:
        assert len(sanitize(CUSTOMER_MAIL)) == MAX_MESSAGE_CHARS and sanitize(CUSTOMER_MAIL).endswith("…")
