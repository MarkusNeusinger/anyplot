"""Tests for agents/anyplot/contact_filter.py: web addresses, e-mail addresses and phone numbers in text.

The must-catch probes are the ones the guardrail review of 2026-10-10 found passing: a
code-name subdomain in front of an attacker's domain, word and file country codes
without a path, abused generic domains, German phone formats and Unicode spaces. The
must-pass probes are code, file names, dates, ids and ranges that a reply or a plot
label carries.
"""

import pytest

from agents.anyplot.contact_filter import (
    COUNTRY_TLDS,
    FILE_TLDS,
    PATH_ONLY_TLDS,
    TLDS,
    contact_kinds,
    find_contacts,
    has_contact,
    strip_contacts,
)


def found(text: str) -> list[tuple[str, str]]:
    return [(contact.kind, text[contact.start : contact.end]) for contact in find_contacts(text)]


class TestWebAddresses:
    @pytest.mark.parametrize(
        ("text", "host"),
        [
            ("Visit securebank.com/login to claim your prize", "securebank.com/login"),
            ("pay the 1.99 fee at parcel-help.com/pay to release it.", "parcel-help.com/pay"),
            ("see www.example.de", "www.example.de"),
            ("example.co.uk", "example.co.uk"),
            ("bit.ly/abc", "bit.ly/abc"),
            ("t.me/channel", "t.me/channel"),
            ("Shop at deals.top now", "deals.top"),
            ("docs on matplotlib.org", "matplotlib.org"),
            ("SECUREBANK.COM", "SECUREBANK.COM"),
            ("host.example.com:8080/x", "host.example.com:8080/x"),
            ("Visit parcel-help.review", "parcel-help.review"),
            ("parcel-help.zone today", "parcel-help.zone"),
        ],
    )
    def test_hosts_are_found(self, text: str, host: str) -> None:
        assert found(text) == [("web", host)]

    @pytest.mark.parametrize(
        ("text", "host"),
        [
            ("Pay at ax.parcel-help.de/pay", "ax.parcel-help.de/pay"),
            ("stats.parcel-help.shop/pay", "stats.parcel-help.shop/pay"),
            ("df.securebank.xyz/login", "df.securebank.xyz/login"),
            ("self.dhl-zoll.de", "self.dhl-zoll.de"),
            ("os.inpost-oplata.pl/pay", "os.inpost-oplata.pl/pay"),
            ("np.securebank.co.uk", "np.securebank.co.uk"),
            ("ax.securebank.de", "ax.securebank.de"),
            ("math.win/prize", "math.win/prize"),
        ],
    )
    def test_a_code_name_subdomain_does_not_hide_a_host(self, text: str, host: str) -> None:
        assert found(text) == [("web", host)]

    @pytest.mark.parametrize(
        ("text", "host"),
        [
            ("Zahlung unter dhl-zoll.at", "dhl-zoll.at"),
            ("Pay at inpost-doplata.pl", "inpost-doplata.pl"),
            ("Visit paypal-verify.us", "paypal-verify.us"),
            ("Visit sbi-kyc.in", "sbi-kyc.in"),
            ("Visit shop.dhl.at", "shop.dhl.at"),
            ("Visit DHL-ZOLL.AT", "DHL-ZOLL.AT"),
        ],
    )
    def test_a_word_country_code_counts_with_a_registered_looking_name(self, text: str, host: str) -> None:
        assert found(text) == [("web", host)]

    def test_a_trailing_full_stop_is_not_part_of_the_path(self) -> None:
        assert found("Go to parcel-help.com/pay.") == [("web", "parcel-help.com/pay")]

    @pytest.mark.parametrize(
        "text",
        [
            "plot.py",
            "my-plot.py",
            "run plot.py with data.csv",
            "plot-light.png",
            "README.md",
            "df.at[0, 'x']",
            "plt.cm.viridis",
            "np.ma.masked",
            "pd.NA",
            "ax.spines.top",
            "ax.spines.top/right are hidden",
            "fig.subplotpars.top",
            "self.title.top",
            "g.ax.set_title('x')",
            "series.name",
            "row.name",
            "event.date",
            "Run df.info() to list the columns.",
            "data.info() lists the columns.",
            "df.info to list",
            "values.top 5",
            "item.link",
            "data.click",
            "e.g. the title",
            "i.e. not this",
            "U.S. sales",
            "Ph.D. thesis",
            "the plot.It shows",
            "the long-term.It shows",
            "v1.2.3",
            "3.14",
            "1.2.de",
        ],
    )
    def test_code_file_names_and_prose_are_not_hosts(self, text: str) -> None:
        assert found(text) == []

    def test_a_word_or_file_tld_counts_with_a_path(self) -> None:
        assert found("plot.py") == [] and found("evil.me/x") == [("web", "evil.me/x")]

    def test_the_tld_lists(self) -> None:
        assert len(COUNTRY_TLDS) > 240 and all(len(tld) == 2 for tld in COUNTRY_TLDS)
        assert {"com", "net", "org", "top", "xyz", "de", "uk", "review", "party", "zone", "fyi"} <= TLDS
        assert FILE_TLDS <= PATH_ONLY_TLDS <= COUNTRY_TLDS
        assert not {"name", "int", "cat", "style", "show", "map", "date"} & TLDS


class TestFolding:
    @pytest.mark.parametrize(
        ("text", "kind", "span"),
        [
            ("Call +49 30 1234567 now", "phone", "+49 30 1234567"),
            ("Visit parcel-help。de now", "web", "parcel-help。de"),
            ("Visit parcel​-help.de/pay now", "web", "parcel​-help.de/pay"),
            ("Write to support＠securebank.com", "email", "support＠securebank.com"),
            ("Call 0800–123–4567 now", "phone", "0800–123–4567"),
            ("ｐａｒｃｅｌ-help.com/pay", "web", "ｐａｒｃｅｌ-help.com/pay"),
        ],
    )
    def test_unicode_variants_are_found_with_their_original_span(self, text: str, kind: str, span: str) -> None:
        assert found(text) == [(kind, span)]

    def test_stripping_works_on_the_original_text(self) -> None:
        assert strip_contacts("Call +49 30 1234567 today…") == "Call today…"


class TestEmailAndPhone:
    def test_email(self) -> None:
        assert found("write to support@securebank.com today") == [("email", "support@securebank.com")]

    @pytest.mark.parametrize(
        "number",
        [
            "+1 555 0100",
            "+49 30 1234567",
            "+1 (555) 010-0100",
            "+44 20 7946 0958",
            "0049 30 1234567",
            "(+49) 30 1234567",
            "+49 30 / 1234567",
            "030 1234567",
            "030 / 123 456 78",
            "0800-123-4567",
            "089/1234567",
            "(030) 123456",
            "(212) 555-0100",
            "212-555-0100",
            "1-800-555-0100",
            "0151 23456789",
        ],
    )
    def test_phone_numbers(self, number: str) -> None:
        assert found(f"Call {number} now") == [("phone", number)]

    @pytest.mark.parametrize(
        ("text", "number"),
        [
            ("Call 0301234567", "0301234567"),
            ("Call 01701234567 now", "01701234567"),
            ("Tel.: 0301234567", "0301234567"),
            ("Call 800 555 0100", "800 555 0100"),
        ],
    )
    def test_numbers_a_phone_word_marks(self, text: str, number: str) -> None:
        assert found(text) == [("phone", number)]

    @pytest.mark.parametrize(
        "text",
        [
            "2024-01-15",
            "01.02.2024",
            "values 0.25 0.5 0.75",
            "2000 2005 2010 2015",
            "Sales (2024) 1500 2000",
            "r = 0.83",
            "+12.5%",
            "1,234,567",
            "x from 1990-2020",
            "Range 1990–2020",
            "Q1 2024: 12.5k",
            "n = 5000",
            "from 10:00 - 12:00",
            "ticks at 200 500 1000",
            "costs 1 234 567 EUR",
            "Order 2024-001-0042 is the largest value.",
            "Label the order 2024-001-0042 in the subtitle",
            "Show the range 100-200-3000",
            "ids 0012345678 and 0098765432",
        ],
    )
    def test_dates_numbers_ids_and_ranges_are_not_phones(self, text: str) -> None:
        assert found(text) == []


class TestHelpers:
    def test_has_contact_and_kinds(self) -> None:
        text = "Mail a@b.org, call +1 555 0100, see c.com"

        assert has_contact(text) and contact_kinds(text) == ["web", "email", "phone"]
        assert not has_contact("Make the bars blue") and contact_kinds("Make the bars blue") == []

    def test_strip_takes_one_space_with_each(self) -> None:
        assert strip_contacts("Visit securebank.com/login to claim") == "Visit to claim"
        assert strip_contacts("Amazon.com sales") == "sales"  # a brand that is a domain counts as one
        assert strip_contacts("Write to support@x.org, then wait.") == "Write to, then wait."
        assert strip_contacts("no contact here  at all") == "no contact here  at all"
        assert (
            strip_contacts("Order 2024-001-0042 is the largest value.") == "Order 2024-001-0042 is the largest value."
        )
