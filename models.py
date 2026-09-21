from pydantic import BaseModel, Field, field_validator


class UserIdentifier(BaseModel):
    user_id: str = Field(min_length=8)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value):
        value = value.strip()
        if any(character.isspace() for character in value):
            raise ValueError("Identifier cannot contain spaces.")
        if not any(character.isdigit() for character in value):
            raise ValueError("Identifier must include a number.")
        if not any(not character.isalnum() for character in value):
            raise ValueError("Identifier must include a special character.")
        return value
