"""Tests for agents/anyplot/contact_filter.py: web addresses, e-mail addresses and phone numbers in text."""

import pytest

from agents.anyplot.contact_filter import (
    COUNTRY_TLDS,
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
        ],
    )
    def test_hosts_are_found(self, text: str, host: str) -> None:
        assert found(text) == [("web", host)]

    def test_a_trailing_full_stop_is_not_part_of_the_path(self) -> None:
        assert found("Go to parcel-help.com/pay.") == [("web", "parcel-help.com/pay")]

    @pytest.mark.parametrize(
        "text",
        [
            "plot.py",
            "run plot.py with data.csv",
            "plot-light.png",
            "README.md",
            "df.at[0, 'x']",
            "plt.cm.viridis",
            "np.ma.masked",
            "pd.NA",
            "ax.spines.top",
            "series.name",
            "e.g. the title",
            "i.e. not this",
            "U.S. sales",
            "Ph.D. thesis",
            "the plot.It shows",
            "v1.2.3",
            "3.14",
        ],
    )
    def test_code_file_names_and_prose_are_not_hosts(self, text: str) -> None:
        assert found(text) == []

    def test_a_word_or_file_tld_counts_with_a_path(self) -> None:
        assert found("plot.py") == [] and found("evil.me/x") == [("web", "evil.me/x")]

    def test_the_tld_lists(self) -> None:
        assert len(COUNTRY_TLDS) > 240 and all(len(tld) == 2 for tld in COUNTRY_TLDS)
        assert {"com", "net", "org", "top", "xyz", "de", "uk"} <= TLDS
        assert PATH_ONLY_TLDS <= COUNTRY_TLDS
        assert not {"name", "int", "cat", "style", "show", "map"} & TLDS


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
            "030 1234567",
            "0800-123-4567",
            "089/1234567",
            "(030) 123456",
            "(555) 010-0100",
            "555-010-0100",
            "1-800-555-0100",
            "0151 23456789",
        ],
    )
    def test_phone_numbers(self, number: str) -> None:
        assert found(f"Call {number} now") == [("phone", number)]

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
            "Q1 2024: 12.5k",
            "n = 5000",
        ],
    )
    def test_dates_numbers_and_ranges_are_not_phones(self, text: str) -> None:
        assert found(text) == []


class TestHelpers:
    def test_has_contact_and_kinds(self) -> None:
        text = "Mail a@b.org, call +1 555 0100, see c.com"

        assert has_contact(text) and contact_kinds(text) == ["web", "email", "phone"]
        assert not has_contact("Make the bars blue") and contact_kinds("Make the bars blue") == []

    def test_strip_takes_one_space_with_each(self) -> None:
        assert strip_contacts("Visit securebank.com/login to claim") == "Visit to claim"
        assert strip_contacts("Amazon.com sales") == "sales"
        assert strip_contacts("Write to support@x.org, then wait.") == "Write to, then wait."
        assert strip_contacts("no contact here  at all") == "no contact here  at all"
