from typing import TypeVar, get_type_hints
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

M = TypeVar("M", bound=BaseModel)


def is_pydantic_model(annotation) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def create_combined_model(
    __name__: str,
    /,  # makes __name__ positional only
    *models: tuple[type[M], ...],
) -> type[M]:
    field_overrides = {}

    # Gather all field annotations from all models
    all_fields: dict[str, list] = {}
    for model in models:
        model_fields = get_type_hints(model)
        for name, annotation in model_fields.items():
            if name in all_fields:
                all_fields[name].append(annotation)
            else:
                all_fields[name] = [annotation]

    for name, annotations in all_fields.items():
        # Get the first annotation as a reference
        base_annotation = annotations[0]

        if all(is_pydantic_model(annotation) for annotation in annotations):
            # All annotations are Pydantic models
            for annotation in annotations:
                assert annotation is base_annotation, f"{name} has different types in the models"
            sub_model = create_combined_model(
                f"Combined{''.join([ann.__name__ for ann in annotations])}",
                *annotations,
            )
            field_overrides[name] = (sub_model, FieldInfo())
        else:
            # Ensure all annotations are identical
            for annotation in annotations:
                assert annotation == base_annotation, f"Different types for field {name}"
            field_overrides[name] = (base_annotation, FieldInfo())

    return create_model(__name__, __base__=models, **field_overrides)  # type: ignore
