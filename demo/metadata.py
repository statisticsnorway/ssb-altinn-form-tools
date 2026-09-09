import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

from ssb_altinn_form_tools.utils.form_metadata import FormMetadata

fetcher = FormMetadata("RA0485")
fetcher.extract_options_list("RA0485", "2025")
