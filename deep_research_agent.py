"""
Deep Research Agent

This application combines the OpenAI Agents SDK with FireCrawl to create a powerful
research assistant that can answer questions on any topic by gathering and analyzing
information from the web.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Import OpenAI Agents SDK
from agents import Agent, Runner, function_tool

# Import FireCrawl SDK
# Nota: La forma de importar puede variar según la versión de FireCrawl
# Si encuentras errores, prueba con:
# from firecrawl import WebToTextExtractor, FirecrawlApp
try:
    from firecrawl.web_to_text import WebToTextExtractor
    from firecrawl.firecrawl import FirecrawlApp
except ImportError:
    try:
        from firecrawl import WebToTextExtractor, FirecrawlApp
    except ImportError:
        raise ImportError("No se pudo importar FireCrawl. Asegúrate de tenerlo instalado con 'pip install firecrawl'")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepResearchAgent:
    """
    A research agent that combines OpenAI Agents with FireCrawl to perform deep research
    on any topic.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, use_local_docker: bool = True, firecrawl_api_key: Optional[str] = None):
        """
        Initialize the DeepResearchAgent.
        
        Args:
            openai_api_key: OpenAI API key (if None, will try to get from environment)
            use_local_docker: Whether to use a local Docker instance for FireCrawl
            firecrawl_api_key: FireCrawl API key for cloud API (if None, will try to get from environment)
        """
        # Set OpenAI API key
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Please provide it or set OPENAI_API_KEY environment variable.")
        
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        
        # Initialize FireCrawl extractor
        if use_local_docker:
            logger.info("Initializing FireCrawl with local Docker")
            try:
                self.extractor = WebToTextExtractor.create_with_local_docker()
                logger.info("Successfully initialized FireCrawl with local Docker")
            except Exception as e:
                logger.error(f"Error initializing FireCrawl with local Docker: {str(e)}")
                logger.info("Falling back to cloud API...")
                self.extractor = self._initialize_cloud_api(firecrawl_api_key)
        else:
            logger.info("Initializing FireCrawl with cloud API")
            self.extractor = self._initialize_cloud_api(firecrawl_api_key)
        
        # Initialize agents
        self.agents = self._create_agents()
        logger.info("Initialized OpenAI Agents")
    
    def _initialize_cloud_api(self, firecrawl_api_key: Optional[str] = None):
        """
        Initialize FireCrawl with cloud API.
        
        Args:
            firecrawl_api_key: FireCrawl API key (if None, will try to get from environment)
            
        Returns:
            WebToTextExtractor instance
        """
        api_key = firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            logger.warning("No FireCrawl API key provided. Some features may not work properly.")
            return WebToTextExtractor()
        else:
            logger.info("Using FireCrawl cloud API with provided API key")
            return WebToTextExtractor(api_key=api_key)
    
    def _create_agents(self):
        """
        Create the agents used in the deep research system.
        
        Returns:
            Dictionary of agents
        """
        # Define tool functions that don't include 'self' parameter
        @function_tool()
        async def generate_search_queries(topic: str, num_queries: Optional[int] = None) -> List[str]:
            """
            Generate search queries for a given topic.
            
            Args:
                topic: The main topic or question to research
                num_queries: Number of search queries to generate (default: 3)
            """
            actual_num_queries = 3 if num_queries is None else num_queries
            return await self._generate_search_queries(topic, actual_num_queries)
        
        @function_tool()
        async def search_web(query: str, num_results: Optional[int] = None) -> str:
            """
            Search the web for information on a topic.
            
            Args:
                query: The search query
                num_results: Number of results to return (default: 5)
            """
            actual_num_results = 5 if num_results is None else num_results
            return await self._search_web(query, actual_num_results)
        
        @function_tool()
        async def deep_research_topic(query: str, max_depth: Optional[int] = None, time_limit: Optional[int] = None) -> str:
            """
            Perform deep research on a topic by searching and following links.
            
            Args:
                query: The research query
                max_depth: Maximum depth of link following (default: 5)
                time_limit: Time limit in seconds (default: 180)
            """
            actual_max_depth = 5 if max_depth is None else max_depth
            actual_time_limit = 180 if time_limit is None else time_limit
            return await self._deep_research_topic(query, actual_max_depth, actual_time_limit)
        
        @function_tool()
        async def extract_from_url(url: str) -> str:
            """
            Extract content from a specific URL.
            
            Args:
                url: The URL to extract content from
            """
            return await self._extract_from_url(url)
        
        @function_tool()
        async def search_and_extract(query: str, num_results: Optional[int] = None) -> str:
            """
            Search for content and extract from the top results.
            
            Args:
                query: The search query
                num_results: Number of results to extract from (default: 3)
            """
            actual_num_results = 3 if num_results is None else num_results
            return await self._search_and_extract(query, actual_num_results)
            
        # Create research planner agent
        research_planner = Agent(
            name="ResearchPlanner",
            instructions="""You are a research planning expert. Your job is to:
            1. Analyze the user's question to understand what they want to know
            2. Break down complex questions into specific research queries
            3. Determine the best search queries to find relevant information
            4. Create a research plan with multiple angles to explore
            
            Be thorough and consider different perspectives on the topic.
            """,
            tools=[generate_search_queries],
            model="gpt-4o",
        )
        
        # Create web researcher agent
        web_researcher = Agent(
            name="WebResearcher",
            instructions="""You are a web research expert. Your job is to:
            1. Execute search queries to find relevant information on the web
            2. Extract key information from search results
            3. Follow up with deeper research on specific subtopics when needed
            4. Compile comprehensive information from multiple sources
            
            Always cite your sources and be thorough in your research.
            """,
            tools=[
                search_web, 
                deep_research_topic, 
                extract_from_url,
                search_and_extract
            ],
            model="gpt-4o",
        )
        
        # Create synthesis agent
        synthesis_agent = Agent(
            name="SynthesisAgent",
            instructions="""You are an information synthesis expert. Your job is to:
            1. Analyze research findings from multiple sources
            2. Identify key insights and patterns
            3. Reconcile conflicting information when present
            4. Create a comprehensive, well-structured response to the original question
            
            Your response should be thorough, accurate, and easy to understand. Include citations
            to sources where appropriate. Organize information logically and highlight the most
            important points.
            """,
            tools=[],  # Synthesis agent doesn't need tools, just processes information
            model="gpt-4o",
        )
        
        return {
            "planner": research_planner,
            "researcher": web_researcher,
            "synthesis": synthesis_agent
        }
    
    # FireCrawl Tool Functions (internal implementation)
    async def _generate_search_queries(self, topic: str, num_queries: int = 3) -> List[str]:
        """
        Generate search queries for a given topic.
        
        Args:
            topic: The main topic or question to research
            num_queries: Number of search queries to generate
            
        Returns:
            List of search queries
        """
        # This function doesn't actually use FireCrawl, but helps the planner agent
        # We'll just return the input as the first query, and let the agent generate the rest
        return [topic]
    
    async def _search_web(self, query: str, num_results: int = 5) -> str:
        """
        Search the web for information on a topic.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            Search results as formatted text
        """
        try:
            logger.info(f"Searching web for: {query}")
            results = self.extractor.search_and_extract(
                query=query,
                limit=num_results,
                formats=["markdown"]
            )
            
            # Format the results
            formatted_results = ""
            for i, result in enumerate(results, 1):
                url = result.get("search_metadata", {}).get("url", "Unknown URL")
                title = result.get("search_metadata", {}).get("title", f"Result {i}")
                
                formatted_results += f"## {title}\n"
                formatted_results += f"Source: {url}\n\n"
                
                if "markdown" in result:
                    # Limit content length to avoid token issues
                    content = result["markdown"]
                    if len(content) > 2000:
                        content = content[:2000] + "...[content truncated]"
                    formatted_results += content + "\n\n"
                else:
                    formatted_results += "No content extracted\n\n"
            
            if not results:
                return "No search results found."
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in search_web: {str(e)}")
            return f"Error searching the web: {str(e)}"
    
    async def _deep_research_topic(self, query: str, max_depth: int = 5, time_limit: int = 180) -> str:
        """
        Perform deep research on a topic by searching and following links.
        
        Args:
            query: The research query
            max_depth: Maximum depth of link following
            time_limit: Time limit in seconds
            
        Returns:
            Research results as formatted text
        """
        try:
            logger.info(f"Starting deep research on: {query}")
            research_results = self.extractor.deep_research(
                query=query,
                max_depth=max_depth,
                max_urls=10,
                time_limit=time_limit
            )
            
            if not research_results.get("success", False):
                return f"Deep research failed: {research_results.get('error', 'Unknown error')}"
            
            # Format the results
            formatted_results = "# Deep Research Results\n\n"
            
            # Add summaries
            summaries = research_results.get("summaries", [])
            if summaries:
                formatted_results += "## Summaries\n\n"
                for i, summary in enumerate(summaries, 1):
                    formatted_results += f"### Summary {i}\n{summary}\n\n"
            
            # Add sources
            sources = research_results.get("sources", [])
            if sources:
                formatted_results += "## Sources\n\n"
                for i, source in enumerate(sources, 1):
                    url = source.get("url", "Unknown URL")
                    title = source.get("title", f"Source {i}")
                    formatted_results += f"{i}. [{title}]({url})\n"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in deep_research_topic: {str(e)}")
            return f"Error performing deep research: {str(e)}"
    
    async def _extract_from_url(self, url: str) -> str:
        """
        Extract content from a specific URL.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Extracted content as formatted text
        """
        try:
            logger.info(f"Extracting content from URL: {url}")
            result = self.extractor.extract_from_url(
                url=url,
                formats=["markdown"],
                extract_metadata=True
            )
            
            # Format the result
            formatted_result = f"# Content from {url}\n\n"
            
            metadata = result.get("metadata", {})
            if metadata:
                title = metadata.get("title", "")
                if title:
                    formatted_result += f"## {title}\n\n"
            
            if "markdown" in result:
                # Limit content length to avoid token issues
                content = result["markdown"]
                if len(content) > 3000:
                    content = content[:3000] + "...[content truncated]"
                formatted_result += content
            else:
                formatted_result += "No content extracted"
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in extract_from_url: {str(e)}")
            return f"Error extracting content from URL: {str(e)}"
    
    async def _search_and_extract(self, query: str, num_results: int = 3) -> str:
        """
        Search for content and extract from the top results.
        
        Args:
            query: The search query
            num_results: Number of results to extract from
            
        Returns:
            Extracted content as formatted text
        """
        try:
            logger.info(f"Searching and extracting for: {query}")
            results = self.extractor.search_and_extract(
                query=query,
                limit=num_results,
                formats=["markdown"]
            )
            
            # Use the combine_results_for_llm method to format the results
            combined_content = self.extractor.combine_results_for_llm(
                results=results,
                format="markdown",
                include_metadata=True
            )
            
            # Limit content length to avoid token issues
            if len(combined_content) > 4000:
                combined_content = combined_content[:4000] + "...[content truncated]"
            
            return combined_content
            
        except Exception as e:
            logger.error(f"Error in search_and_extract: {str(e)}")
            return f"Error searching and extracting: {str(e)}"
    
    async def research(self, question: str) -> str:
        """
        Perform deep research on a question using a multi-agent approach.
        
        Args:
            question: The user's question or research topic
            
        Returns:
            Comprehensive research results
        """
        try:
            logger.info(f"Starting research on question: {question}")
            
            # Step 1: Use the planner agent to analyze the question and create a research plan
            logger.info("Step 1: Planning research")
            planning_result = await Runner.run(
                starting_agent=self.agents["planner"],
                input=f"I need to research this topic thoroughly: {question}\n\nPlease analyze this question and create a research plan with specific search queries to investigate.",
            )
            
            from agents.items import ItemHelpers
            planning_output = ItemHelpers.text_message_outputs(planning_result.new_items)
            logger.info(f"Planning complete: {len(planning_output)} characters of output")
            
            # Step 2: Use the researcher agent to gather information
            logger.info("Step 2: Gathering information")
            research_result = await Runner.run(
                starting_agent=self.agents["researcher"],
                input=f"I need to research this topic: {question}\n\nHere's the research plan and queries from our planning phase:\n\n{planning_output}\n\nPlease conduct thorough research using these queries and gather comprehensive information.",
            )
            
            research_output = ItemHelpers.text_message_outputs(research_result.new_items)
            logger.info(f"Research complete: {len(research_output)} characters of output")
            
            # Step 3: Use the synthesis agent to create a final response
            logger.info("Step 3: Synthesizing information")
            synthesis_result = await Runner.run(
                starting_agent=self.agents["synthesis"],
                input=f"Original question: {question}\n\nResearch findings:\n\n{research_output}\n\nPlease synthesize this information into a comprehensive, well-structured answer to the original question.",
            )
            
            final_output = ItemHelpers.text_message_outputs(synthesis_result.new_items)
            logger.info(f"Synthesis complete: {len(final_output)} characters of output")
            
            return final_output
            
        except Exception as e:
            logger.error(f"Error in research: {str(e)}")
            return f"Error performing research: {str(e)}"

def save_research_results(topic: str, results: str):
    """
    Save research results to a Markdown file.
    
    Args:
        topic: The research topic or question
        results: The research results text
    """
    # Create a sanitized filename from the topic
    sanitized_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)
    sanitized_topic = sanitized_topic[:50]  # Limit length
    
    # Create a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create the filename
    filename = f"research_{sanitized_topic}_{timestamp}.md"
    
    # Create the content
    content = f"""# Research Results: {topic}

## Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{results}
"""
    
    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Research results saved to {filename}")
    return filename

# Command-line interface
async def main():
    """
    Command-line interface for the DeepResearchAgent.
    """
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Warning: OPENAI_API_KEY environment variable not set.")
        openai_api_key = input("Please enter your OpenAI API key: ")
    
    # Initialize the agent
    try:
        agent = DeepResearchAgent(openai_api_key=openai_api_key, use_local_docker=True)
        print("Deep Research Agent initialized successfully!")
        
        while True:
            # Get user question
            question = input("\nEnter your research question (or 'quit' to exit): ")
            if question.lower() in ["quit", "exit", "q"]:
                break
            
            print("\nResearching... (this may take a few minutes)")
            
            # Perform research
            result = await agent.research(question)
            
            print("\n" + "="*80 + "\n")
            print("RESEARCH RESULTS:")
            print("\n" + "="*80 + "\n")
            print(result)
            print("\n" + "="*80 + "\n")
            
            # Save results to file
            filename = save_research_results(question, result)
            print(f"\nResults saved to: {filename}")
            
    except Exception as e:
        print(f"Error initializing or running the Deep Research Agent: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
