class EmailData:
    def __init__(
        self,
        from_address: str | None = None,
        to_address: str | None = None,
        subject: str | None = None,
        body: str | None = None
    ):
        self.from_address = from_address
        self.to_address = to_address
        self.subject = subject
        self.body = body

    def __repr__(self):
        return (
            f"EmailData(from={self.from_address!r}, "
            f"to={self.to_address!r}, "
            f"subject={self.subject!r}, "
            f"body={self.body!r})"
        )
