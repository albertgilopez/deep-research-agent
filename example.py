"""
Ejemplo de uso del DeepResearch Agent

Este script muestra cómo utilizar el DeepResearch Agent de manera programática.
"""

import os
import asyncio
from dotenv import load_dotenv
from deep_research_agent import DeepResearchAgent

# Cargar variables de entorno desde .env (si existe)
load_dotenv()

async def main():
    # Obtener la API key de OpenAI (desde variable de entorno o solicitar al usuario)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = input("Por favor, introduce tu API key de OpenAI: ")
    
    # Inicializar el agente
    print("Inicializando DeepResearch Agent...")
    agent = DeepResearchAgent(openai_api_key=openai_api_key, use_local_docker=True)
    
    # Ejemplo de pregunta de investigación
    question = "¿Cuáles son las últimas tendencias en inteligencia artificial generativa?"
    
    print(f"\nInvestigando: {question}")
    print("Esto puede tardar unos minutos...")
    
    # Realizar la investigación
    result = await agent.research(question)
    
    # Mostrar resultados
    print("\n" + "="*80)
    print("RESULTADOS DE LA INVESTIGACIÓN:")
    print("="*80 + "\n")
    print(result)
    print("\n" + "="*80)
    
    # Guardar resultados en un archivo
    from deep_research_agent import save_research_results
    filename = save_research_results(question, result)
    print(f"\nResultados guardados en: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
