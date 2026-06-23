import glob
import logging
import os

logging.basicConfig(
    level=logging.DEBUG,  # Set minimum log level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

import polars as pl

from ssb_altinn_form_tools.default_form_extractor import DefaultFormExtractor
from ssb_altinn_form_tools.default_form_extractor import parse_entries
from ssb_altinn_form_tools.default_form_processor import DefaultFormProcessor
from ssb_altinn_form_tools.meta_form_extractor import InputFormType
from ssb_altinn_form_tools.meta_storage_connector import MetaStorageConnector
from ssb_altinn_form_tools.models import ContactInfo
from ssb_altinn_form_tools.models import FormData
from ssb_altinn_form_tools.models import FormReception
from ssb_altinn_form_tools.models import OptionMetadataModel
from ssb_altinn_form_tools.models import OptionNodes
from ssb_altinn_form_tools.models import Unit
from ssb_altinn_form_tools.models import UnitInfo


class CustomExtractor(DefaultFormExtractor):
    def extract_form_data(
        self,
        form_dict_data: InputFormType,
        form: str,
        ident: str,
        refnr: str,
        iso_period: str,
    ) -> list[FormData]:
        assert isinstance(form_dict_data, dict)
        form_data = {**form_dict_data["SkjemaData"], **form_dict_data["InternInfo"]}

        entries = parse_entries(form_data)
        data = []
        for entry in entries:
            form_data = FormData.from_form_data(
                entry, form=form, ident=ident, refnr=refnr, iso_period=iso_period
            )
            data.append(form_data)
        return data


class ParquetFileConnector(MetaStorageConnector):
    def __init__(
        self,
        base_storage_path: str,
        # per_form: bool = False,
        base_filename: str,
        per_period: bool = False,
        per_file: bool = False,
    ) -> None:
        if (per_file is False) and (per_period is False):
            raise ValueError("One of per period or per file must be true")

        self._per_period = per_period
        self._per_file = per_file
        self._base_storage_path = base_storage_path
        self._base_filename = base_filename

        self._schema = {
            "iso_period": pl.String,
            "skjema": pl.String,
            "ident": pl.String,
            "refnr": pl.String,
            "feltsti": pl.String,
            "feltnavn": pl.String,
            "verdi": pl.String,
            "dybde": pl.Int32,
            "indeks": pl.Int32,
            "alias": pl.String,
        }

    def validate_form_is_new(self, form_reference: str) -> bool:
        if hasattr(self, "_previous_forms") is False:
            files = glob.glob(f"{self._base_storage_path}/*.parquet")
            self._previous_forms = (
                pl.scan_parquet(files, schema=self._schema)
                .select("refnr")
                .collect()
                .get_column("refnr")
                .unique()
                .to_list()
            )
        return form_reference not in self._previous_forms

    def begin_transaction(self) -> None:
        self.file = pl.DataFrame(schema=self._schema)

    def rollback(self) -> None:
        self.file = pl.DataFrame(schema=self._schema)

    def commit(self) -> None:
        if self._per_file:
            new_refnr = self.file.get_column("refnr").unique().to_list()
            for refnr in new_refnr:
                filename = (
                    f"{self._base_storage_path}/{self._base_filename}_{refnr}.parquet"
                )
                if os.path.exists(filename) is False:
                    os.makedirs(self._base_storage_path, exist_ok=True)
                    self.file.filter(pl.col("refnr") == refnr).write_parquet(filename)

        if self._per_period:
            new_periods = self.file.get_column("iso_period").unique().to_list()
            new_refnr = self.file.get_column("refnr").unique().to_list()
            for period in new_periods:
                filename = (
                    f"{self._base_storage_path}/{self._base_filename}_{period}.parquet"
                )

                if os.path.exists(filename) is False:
                    os.makedirs(self._base_storage_path, exist_ok=True)
                    self.file.filter(pl.col("iso_period") == period).write_parquet(
                        filename
                    )
                else:
                    existing_file = pl.read_parquet(filename, schema=self._schema)
                    existing_refnr = (
                        existing_file.get_column("refnr").unique().to_list()
                    )

                    new_entries = []
                    for refnr in new_refnr:
                        if refnr not in existing_refnr:
                            subset = self.file.filter(pl.col("refnr") == refnr)
                            new_entries.append(subset)

                    pl.concat([existing_file, *new_entries]).write_parquet(filename)

    def insert_form_data(self, form_data: list[FormData]) -> None:
        new_data = pl.DataFrame(
            [model.model_dump() for model in form_data], schema=self._schema
        )
        self.file = pl.concat([self.file, new_data])

    def insert_contact_info(self, contact_info: list[ContactInfo]) -> None:
        pass

    def insert_form_data_unedited(self, form_data: list[FormData]) -> None:
        pass

    def insert_form_reception(self, form_reciept: list[FormReception]) -> None:
        pass

    def insert_option_list(self, models: list[OptionMetadataModel]) -> None:
        pass

    def insert_option_node(self, models: list[OptionNodes]) -> None:
        pass

    def insert_unit(self, unit: list[Unit]) -> None:
        pass

    def insert_unit_info(self, units: list[UnitInfo]) -> None:
        pass

    def create_tables_if_not_exists(self) -> None:
        pass

    def validate_options_exists(self, skjema: str, iso_period: str | None) -> bool:
        return True


if __name__ == "__main__":
    connector = ParquetFileConnector("./parqq", "test", per_period=True)
    extractor = CustomExtractor()
    processor = DefaultFormProcessor(
        "RA0485",
        "../tests/testdata/RA0485",
        extractor=extractor,
        connector=connector,
    )
    processor.process_new_forms()
