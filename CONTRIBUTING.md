# Contributing

Bug reports, new review grids (other subjects, languages, school levels) and new automatic checks are welcome.

- Open an issue first for anything large. Keep the kit dependency-free: the core uses only the Python standard
  library, and model backends are optional.
- Add a test for every new check. Run `python3 -m pytest tests`.
- **Never post real student conversations, phone numbers, names or school names** in an issue, a pull request or
  an example file. Examples must be fictional. If you find personal data in this repository, open a private
  security advisory instead of a public issue.
- New grids: put the "NOT a problem" cases first. They are what keeps the judge from raising false alarms.
- By contributing you agree that your contribution is licensed like the rest of the project (Apache-2.0 for
  code, CC BY 4.0 for grids).
