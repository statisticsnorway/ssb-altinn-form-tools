from .meta_form_extractor import MetaFormExtractor, InputFormType
from .models import ContactInfo, FormNode, FormData, FormReception, UnitInfo

def calc_depth(parent: str | None) -> int | None:
    if parent:
        return len(parent.split("/"))
    else:
        return None

def parse_index(path: str | None) -> int | None: 
    try:
        if path:
            return int(path.split("/")[-2])
        else:
            return None
    except ValueError:
        return None

def parse_entries(data: dict | list, parent: None | str = None) -> list[FormNode]:
    fields = []

    if isinstance(data, list):
        iterator = enumerate(data)
    elif isinstance(data, dict):
        iterator = data.items()

    for key, value in iterator:

        sti = f"{parent if parent else ''}/{key}"
        if isinstance(value, list) or isinstance(value, dict):
            fields.extend(parse_entries(value, parent=sti))

        else:
            parent = str(parent) if parent else ""
            index = parse_index(sti)
            depth = calc_depth(parent)
            fields.append(
                FormNode(
                    feltsti=sti,
                    feltnavn=str(key),
                    verdi=value,
                    dybde=depth,
                    indeks=index,
                )
            )

    return fields


class DefaultFormExtractor(MetaFormExtractor):

    def __init__(self) -> None:
        super().__init__()

    def extract_contact_info(
        self,
        form_dict_data: InputFormType,
        year: int,
        form: str,
        ident: str,
        refnr: str,
    ) -> ContactInfo:
        form_data = form_dict_data["Kontakt"]

        assert isinstance(form_data, dict)

        return ContactInfo(
            aar=year,
            skjema=form,
            ident=ident,
            refnr=refnr,
            bekreftet_kontaktinfo=form_data.get("kontaktInfoBekreftet") == "1",
            **form_data,
        )

    def extract_form_data(
        self,
        form_dict_data: InputFormType,
        year: int,
        form: str,
        ident: str,
        refnr: str,
    ) -> list[FormData]:
        form_data = form_dict_data["SkjemaData"]

        assert isinstance(form_data, dict) or isinstance(form_data, list)
        parsed_form_data = parse_entries(form_data)

        results: list[FormData] = []
        for node in parsed_form_data:
            node_data = FormData(
                aar=year,
                skjema=form,
                ident=ident,
                refnr=refnr,
                **node.model_dump(),
            )
            results.append(node_data)
        return results

    def extract_form_reception(
        self, form_dict_data: InputFormType, json_data: dict
    ) -> FormReception:
        form_data = form_dict_data["InternInfo"]

        assert isinstance(form_data, dict)

        return FormReception(
            editert="ikke editert", kommentar="", aktiv=True, **form_data, **json_data
        )

    def extract_unit_info(
        self, form_dict_data: InputFormType, year: int, ident: str
    ) -> list[UnitInfo]:
        form_data = form_dict_data["InternInfo"]

        assert isinstance(form_data, dict)

        info: list[UnitInfo] = []
        for key, value in form_data.items():
            key: str
            if key.startswith("enhets"):
                data = UnitInfo(aar=year, ident=ident, variabel=key, verdi=value)
                info.append(data)
        return info
