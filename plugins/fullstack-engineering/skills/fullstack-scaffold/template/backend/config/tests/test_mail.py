from backend.config.settings.base import env, mail_sender


def test_the_sender_defaults_to_the_smtp_login():
    """Most SMTP servers refuse any other sender than their login."""
    assert (
        mail_sender("", "mailer@example.com", "Atlas") == "Atlas <mailer@example.com>"
    )


def test_without_an_address_login_the_sender_is_webmaster_at_localhost():
    assert mail_sender("", "", "Atlas") == "Atlas <webmaster@localhost>"
    assert mail_sender("", "apikey", "Atlas") == "Atlas <webmaster@localhost>"


def test_an_override_wins():
    assert mail_sender("Support <help@example.com>", "mailer@example.com", "Atlas") == (
        "Support <help@example.com>"
    )


def test_an_empty_env_value_counts_as_unset(monkeypatch):
    """`DEFAULT_FROM_EMAIL=` in an env file: django-environ returns "", not the default."""
    monkeypatch.setenv("DEFAULT_FROM_EMAIL", "")
    override = env.str("DEFAULT_FROM_EMAIL", default="")

    assert override == ""
    assert mail_sender(override, "mailer@example.com", "Atlas") == (
        "Atlas <mailer@example.com>"
    )
