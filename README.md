# DeepResearch Agent

Este proyecto implementa un agente de investigación avanzado que combina el SDK de OpenAI Agents con FireCrawl para realizar investigaciones profundas sobre cualquier tema. El agente puede buscar información en la web, extraer contenido relevante y sintetizar los resultados en una respuesta coherente y completa.

## Características

- **Arquitectura Multi-Agente**: Utiliza tres agentes especializados (Planner, Researcher y Synthesis) que trabajan en conjunto.
- **Búsqueda Web Avanzada**: Integración con FireCrawl para realizar búsquedas web estructuradas.
- **Investigación Profunda**: Capacidad para seguir enlaces y explorar temas en profundidad.
- **Síntesis de Información**: Combina información de múltiples fuentes en una respuesta coherente.
- **Guardado de Resultados**: Guarda automáticamente los resultados de la investigación en archivos Markdown.

## Requisitos

- Python 3.8+
- OpenAI API Key
- FireCrawl (local vía Docker o API en la nube)

## Instalación

1. Clona este repositorio:
   ```
   git clone https://github.com/albertgilopez/deep-research-agent.git
   cd deep-research-agent
   ```

2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Configura tu API Key de OpenAI:
   ```
   export OPENAI_API_KEY="tu-api-key"
   ```
   En Windows (PowerShell):
   ```
   $env:OPENAI_API_KEY="tu-api-key"
   ```

4. Configuración de FireCrawl:

   Tienes dos opciones para usar FireCrawl:

   **Opción 1: Usar la imagen Docker oficial**
   
   La forma más sencilla de ejecutar FireCrawl localmente es usando la imagen Docker oficial:

   ```
   docker pull firecrawl/firecrawl:latest
   docker run -d -p 8000:8000 firecrawl/firecrawl:latest
   ```

   **Opción 2: Usar la API en la nube**
   
   Alternativamente, puedes usar la API en la nube de FireCrawl. Para ello, necesitarás registrarte en [firecrawl.dev](https://firecrawl.dev) y obtener una API key.
   
   Luego, configura la API key en tu archivo `.env`:
   ```
   FIRECRAWL_API_KEY=tu_api_key_de_firecrawl
   ```

   **Opción 3: Ejecutar FireCrawl desde el código fuente**
   
   Si prefieres ejecutar FireCrawl desde el código fuente, sigue las instrucciones detalladas en la [guía de contribución de FireCrawl](https://docs.firecrawl.dev/contributing/guide).

   Para más información sobre FireCrawl, consulta:
   - [Documentación de FireCrawl - Open Source o Cloud](https://docs.firecrawl.dev/contributing/open-source-or-cloud)
   - [Guía de contribución de FireCrawl](https://docs.firecrawl.dev/contributing/guide)

## Uso

Ejecuta el script principal:

```
python deep_research_agent.py
```

El programa te pedirá que ingreses una pregunta de investigación. Después de procesar la solicitud, mostrará los resultados y los guardará en un archivo Markdown.

### Ejemplo de uso

```python
from deep_research_agent import DeepResearchAgent
import asyncio

async def main():
    agent = DeepResearchAgent()
    result = await agent.research("¿Cuáles son las últimas tendencias en inteligencia artificial generativa?")
    print(result)

asyncio.run(main())
```

## Arquitectura

El sistema utiliza una arquitectura de tres agentes:

1. **Planner Agent**: Analiza la pregunta del usuario y genera un plan de búsqueda con consultas específicas.
2. **Researcher Agent**: Ejecuta las búsquedas web utilizando FireCrawl y recopila información relevante.
3. **Synthesis Agent**: Sintetiza toda la información recopilada en una respuesta coherente y completa.

## Configuración

El agente puede configurarse con los siguientes parámetros:

- `openai_api_key`: Tu API Key de OpenAI.
- `use_local_docker`: Si es `True`, utiliza una instancia local de Docker para FireCrawl. Si es `False`, utiliza la API en la nube.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para sugerir cambios o mejoras.

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).

## Artículo Relacionado

Este proyecto acompaña al artículo de Medium: [Crea tu propio agente DeepResearch con el nuevo SDK Agents de OpenAI y FireCrawl](https://medium.com/@jddam/crea-tu-propio-agente-deepresearch-con-el-nuevo-sdk-agents-de-openai-y-firecrawl-local-9a05e64539ac).

## Autor

[Albert Gil López](https://github.com/albertgilopez)
- GitHub: https://github.com/albertgilopez
- LinkedIn: https://www.linkedin.com/in/albertgilopez/
- M.IA, tu asistente financiero inteligente: https://himia.app/
- Inteligencia Artificial Generativa en español: https://www.codigollm.es/
