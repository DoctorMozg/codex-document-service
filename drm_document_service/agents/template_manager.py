import logging
from pathlib import Path
from typing import Any, cast

import jinja2
from pydantic import BaseModel, Field
from pydantic.types import Annotated

logger = logging.getLogger(__name__)


class TemplateContextSchema(BaseModel):
    variables: Annotated[dict[str, Any], Field(default_factory=dict)]


class TemplateManager:
    QUERIES_DIR = Path("drm_document_service/agents/queries")

    def __init__(self) -> None:
        logger.debug(
            "Initializing TemplateManager with queries directory: %s",
            self.QUERIES_DIR,
        )
        self._env = self._create_environment()

    def _create_environment(self) -> jinja2.Environment:
        logger.debug("Creating Jinja2 environment")
        loader = jinja2.FileSystemLoader(str(self.QUERIES_DIR))
        return jinja2.Environment(
            loader=loader,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(
        self,
        template_name: str,
        context: TemplateContextSchema,
    ) -> str:
        logger.debug("Rendering template: %s", template_name)
        template = self._env.get_template(template_name)
        result = cast(str, template.render(**context.variables))  # type: ignore
        logger.debug("Successfully rendered template: %s", template_name)
        return result

    def render_multiple_templates(
        self,
        template_names: list[str],
        context: TemplateContextSchema,
    ) -> str:
        logger.debug("Rendering multiple templates: %s", template_names)
        rendered_templates = []
        for template_name in template_names:
            rendered = self.render_template(template_name, context)
            rendered_templates.append(rendered)
        result = "\n---\n".join(rendered_templates)
        logger.debug("Successfully rendered %d templates", len(template_names))
        return result


def get_template_manager() -> TemplateManager:
    return TemplateManager()
