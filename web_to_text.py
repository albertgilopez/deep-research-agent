"""
Web to Text Module

This module provides utilities for extracting content from web pages and converting it 
to formats suitable for Large Language Models (LLMs). It builds on the FirecrawlApp
functionality to provide a simplified interface for common web extraction tasks.

Classes:
    - WebToTextExtractor: Main class for extracting web content in LLM-friendly formats.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union, Tuple
import os

from .firecrawl import FirecrawlApp, SearchParams

logger = logging.getLogger("firecrawl.web_to_text")

class WebToTextExtractor:
    """
    A class for extracting web content and converting it to formats suitable for LLMs.
    
    This class provides methods to:
    - Extract content from a single URL
    - Search and extract content from multiple URLs
    - Map a website and extract content from relevant pages
    - Perform deep research on a topic across multiple sources
    """
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, use_local_docker: bool = False):
        """
        Initialize the WebToTextExtractor with the given API credentials.
        
        Args:
            api_key (Optional[str]): API key for Firecrawl. If None, will use FIRECRAWL_API_KEY env var.
                                    Not required when using a local Docker instance.
            api_url (Optional[str]): API URL for Firecrawl. If None, will use default.
            use_local_docker (bool): If True, will use a local Docker instance instead of the cloud service.
                                    This will override api_url to http://localhost:3002 if not specified.
        """
        # If using local Docker and no api_url is specified, use localhost:3002
        if use_local_docker and not api_url:
            api_url = "http://localhost:3002"
            logger.info(f"Using local Docker instance at {api_url}")
        
        # Initialize FirecrawlApp
        # When using local Docker, api_key is optional
        self.app = FirecrawlApp(api_key=api_key, api_url=api_url)
        
        # Store configuration
        self.use_local_docker = use_local_docker
        self.api_url = api_url or self.app.api_url
        
        logger.debug(f"WebToTextExtractor initialized with API URL: {self.api_url}")
        
    def extract_from_url(self, url: str, 
                        formats: List[str] = ['markdown', 'html'],
                        timeout: int = 60000) -> Dict[str, Any]:
        """
        Extract content from a single URL in specified formats.
        
        Args:
            url (str): The URL to extract content from
            formats (List[str]): List of formats to extract. Options: 'markdown', 'html', 'rawHtml', 'links', 'json'
            timeout (int): Timeout in milliseconds
            
        Returns:
            Dict[str, Any]: Dictionary containing the extracted content in requested formats
        """
        # Validate formats to ensure they're compatible with the API
        valid_formats = ['markdown', 'html', 'rawHtml', 'links', 'json', 'screenshot', 'screenshot@fullPage', 'extract']
        validated_formats = [fmt for fmt in formats if fmt in valid_formats]
        
        if not validated_formats:
            # Default to markdown if no valid formats provided
            validated_formats = ['markdown']
        
        # Create params based on whether we're using local Docker or not
        if self.use_local_docker:
            # Parameters for local Docker API (v1)
            params = {
                'formats': validated_formats,
                'timeout': timeout,
                'onlyMainContent': True  # This helps get cleaner content
            }
            
            logger.debug(f"Using Docker API params: {params}")
        else:
            # Parameters for cloud API (v1)
            params = {
                'formats': formats,
                'timeout': timeout
            }
            logger.debug(f"Using Cloud API params: {params}")
        
        try:
            logger.info(f"Extracting content from URL: {url}")
            result = self.app.scrape_url(url, params=params)
            
            # Process the result to make it more LLM-friendly
            processed_result = self._process_scrape_result(result)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Error extracting content from URL {url}: {str(e)}")
            raise
    
    def _extract_metadata_from_markdown(self, markdown_content: str) -> Dict[str, str]:
        """
        Extract basic metadata from markdown content.
        
        Args:
            markdown_content (str): Markdown content
            
        Returns:
            Dict[str, str]: Extracted metadata
        """
        metadata = {}
        
        # Try to extract title (first heading)
        import re
        title_match = re.search(r'# (.*?)(\n|$)', markdown_content)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Try to extract description (first paragraph)
        desc_match = re.search(r'\n\n(.*?)(\n\n|$)', markdown_content)
        if desc_match:
            metadata['description'] = desc_match.group(1).strip()
        
        return metadata
    
    def _process_scrape_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the scrape result to make it more LLM-friendly.
        
        Args:
            result (Dict[str, Any]): The raw scrape result
            
        Returns:
            Dict[str, Any]: Processed result
        """
        processed = {}
        
        # Include the most LLM-friendly formats first
        if 'markdown' in result:
            processed['markdown'] = result['markdown']
        if 'text' in result:
            processed['text'] = result['text']
            
        # Include metadata in a structured format
        if 'metadata' in result:
            processed['metadata'] = {
                'title': result['metadata'].get('title', ''),
                'description': result['metadata'].get('description', ''),
                'author': result['metadata'].get('author', ''),
                'date': result['metadata'].get('date', '')
            }
            
        # Include a summary if available
        if 'summary' in result:
            processed['summary'] = result['summary']
            
        # Include other formats if requested
        for key in result:
            if key not in processed and key not in ['success', 'error']:
                processed[key] = result[key]
                
        return processed
    
    def search_and_extract(self, query: str, 
                          limit: int = 5,
                          formats: List[str] = ['markdown'],
                          country: str = 'us',
                          lang: str = 'en') -> List[Dict[str, Any]]:
        """
        Search for content using the query and extract content from the top results.
        
        Args:
            query (str): The search query
            limit (int): Maximum number of results to return
            formats (List[str]): List of formats to extract from each result
            country (str): Country code for search
            lang (str): Language code for search
            
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing extracted content from each result
        """
        # Validate formats for Docker API if needed
        if self.use_local_docker:
            valid_formats = ['markdown', 'html', 'rawHtml', 'links', 'json', 'screenshot', 'screenshot@fullPage', 'extract']
            validated_formats = [fmt for fmt in formats if fmt in valid_formats]
            if not validated_formats:
                validated_formats = ['markdown']
        else:
            validated_formats = formats
            
        search_params = SearchParams(
            query=query,
            limit=limit,
            country=country,
            lang=lang
        )
        
        try:
            logger.info(f"Searching for: {query}")
            search_results = self.app.search(query, params=search_params)
            
            if not search_results.get('success', False) or 'data' not in search_results:
                logger.error(f"Search failed: {search_results.get('error', 'Unknown error')}")
                return []
                
            extracted_results = []
            for result in search_results['data']:
                url = result.get('url')
                if not url:
                    continue
                    
                try:
                    # Use our updated extract_from_url method which handles Docker compatibility
                    # Only pass formats parameter to avoid issues with API v1
                    extracted = self.extract_from_url(url, formats=validated_formats)
                    # Add search result metadata
                    extracted['search_metadata'] = {
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': url
                    }
                    extracted_results.append(extracted)
                except Exception as e:
                    logger.warning(f"Failed to extract content from {url}: {str(e)}")
                    
            return extracted_results
            
        except Exception as e:
            logger.error(f"Error in search_and_extract: {str(e)}")
            raise
    
    def map_website_and_extract(self, url: str, 
                               search_term: Optional[str] = None,
                               max_pages: int = 5,
                               formats: List[str] = ['markdown']) -> List[Dict[str, Any]]:
        """
        Map a website to find relevant pages and extract content from them.
        
        Args:
            url (str): The base URL of the website
            search_term (Optional[str]): Term to search for within the website
            max_pages (int): Maximum number of pages to extract
            formats (List[str]): List of formats to extract from each page
            
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing extracted content from each page
        """
        # Validate formats for Docker API if needed
        if self.use_local_docker:
            valid_formats = ['markdown', 'html', 'rawHtml', 'links', 'json', 'screenshot', 'screenshot@fullPage', 'extract']
            validated_formats = [fmt for fmt in formats if fmt in valid_formats]
            if not validated_formats:
                validated_formats = ['markdown']
        else:
            validated_formats = formats
            
        try:
            logger.info(f"Mapping website: {url} with search term: {search_term}")
            
            # Map the website
            map_params = {}
            if search_term:
                map_params['search'] = search_term
                
            map_result = self.app.map_url(url, params=map_params)
            
            # Extract URLs from the map result
            urls = []
            if isinstance(map_result, dict) and 'urls' in map_result:
                urls = map_result['urls']
            elif isinstance(map_result, list):
                urls = map_result
                
            # Limit the number of pages
            urls = urls[:max_pages]
            
            # Extract content from each URL
            extracted_results = []
            for page_url in urls:
                try:
                    # Use our updated extract_from_url method which handles Docker compatibility
                    # Only pass formats parameter to avoid issues with API v1
                    extracted = self.extract_from_url(page_url, formats=validated_formats)
                    extracted['url'] = page_url
                    extracted_results.append(extracted)
                except Exception as e:
                    logger.warning(f"Failed to extract content from {page_url}: {str(e)}")
                    
            return extracted_results
            
        except Exception as e:
            logger.error(f"Error in map_website_and_extract: {str(e)}")
            raise
    
    def deep_research(self, query: str, 
                     max_depth: int = 5,
                     max_urls: int = 10,
                     time_limit: int = 180,
                     formats: List[str] = ['markdown']) -> Dict[str, Any]:
        """
        Perform deep research on a topic by searching and following links.
        
        Args:
            query (str): The research query
            max_depth (int): Maximum depth of link following
            max_urls (int): Maximum number of URLs to process
            time_limit (int): Time limit in seconds
            formats (List[str]): List of formats to extract from each page
            
        Returns:
            Dict[str, Any]: Dictionary containing research results
        """
        try:
            logger.info(f"Starting deep research on: {query}")
            
            # Start deep research
            research_params = {
                'maxDepth': max_depth,
                'maxUrls': max_urls,
                'timeLimit': time_limit
            }
            
            research_response = self.app.deep_research(query, params=research_params)
            
            if not research_response.success:
                logger.error(f"Deep research failed: {research_response.error}")
                return {'success': False, 'error': research_response.error}
                
            # Get the research ID
            research_id = research_response.id
            
            # Poll for status until complete
            status = "processing"
            result = None
            
            while status in ["processing", "scraping"]:
                status_response = self.app.deep_research_status(research_id)
                status = status_response.status
                
                if status == "done":
                    # Process the results
                    sources = status_response.sources
                    activities = status_response.activities
                    summaries = status_response.summaries
                    
                    result = {
                        'success': True,
                        'sources': sources,
                        'activities': activities,
                        'summaries': summaries,
                        'research_id': research_id
                    }
                    break
                    
                elif status == "error":
                    logger.error(f"Deep research error: {status_response.error}")
                    return {'success': False, 'error': status_response.error}
                    
                # Wait before polling again
                import time
                time.sleep(2)
                
            return result or {'success': False, 'error': 'Research timed out'}
            
        except Exception as e:
            logger.error(f"Error in deep_research: {str(e)}")
            raise
            
    def generate_llms_text(self, query: str, 
                          max_urls: int = 10,
                          show_full_text: bool = False) -> str:
        """
        Generate LLMs.txt format content from a search query.
        
        Args:
            query (str): The search query
            max_urls (int): Maximum number of URLs to include
            show_full_text (bool): Whether to include full text or just summaries
            
        Returns:
            str: The generated LLMs.txt content
        """
        try:
            logger.info(f"Generating LLMs.txt for query: {query}")
            
            params = {
                'maxUrls': max_urls,
                'showFullText': show_full_text
            }
            
            result = self.app.generate_llms_text(query, params=params)
            
            if isinstance(result, dict) and 'text' in result:
                return result['text']
            elif isinstance(result, str):
                return result
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error generating LLMs.txt: {str(e)}")
            raise
            
    def extract_structured_data(self, url: str, 
                               schema: Optional[Dict[str, Any]] = None,
                               prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract structured data from a URL using a schema or prompt.
        
        Args:
            url (str): The URL to extract data from
            schema (Optional[Dict[str, Any]]): JSON schema for extraction
            prompt (Optional[str]): Prompt for extraction
            
        Returns:
            Dict[str, Any]: The extracted structured data
        """
        try:
            logger.info(f"Extracting structured data from: {url}")
            
            extract_params = {}
            if schema:
                extract_params['schema'] = schema
            if prompt:
                extract_params['prompt'] = prompt
                
            params = {
                'extract': extract_params
            }
            
            result = self.app.scrape_url(url, params=params)
            
            if 'extracted' in result:
                return result['extracted']
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            raise
            
    def combine_results_for_llm(self, results: List[Dict[str, Any]], 
                              format: str = 'markdown',
                              include_metadata: bool = True) -> str:
        """
        Combine multiple extraction results into a single text suitable for LLMs.
        
        Args:
            results (List[Dict[str, Any]]): List of extraction results
            format (str): Format to use ('markdown', 'text')
            include_metadata (bool): Whether to include metadata
            
        Returns:
            str: Combined text suitable for LLMs
        """
        combined = []
        
        for i, result in enumerate(results, 1):
            # Add separator
            combined.append(f"\n{'=' * 80}\n")
            
            # Add source information
            if include_metadata:
                url = result.get('url', '')
                metadata = result.get('metadata', {})
                title = metadata.get('title', f"Source {i}")
                
                combined.append(f"# {title}\n")
                combined.append(f"URL: {url}\n")
                
                if 'description' in metadata and metadata['description']:
                    combined.append(f"Description: {metadata['description']}\n")
                if 'author' in metadata and metadata['author']:
                    combined.append(f"Author: {metadata['author']}\n")
                if 'date' in metadata and metadata['date']:
                    combined.append(f"Date: {metadata['date']}\n")
                
                combined.append("\n")
            
            # Add content
            if format in result:
                combined.append(result[format])
            elif 'markdown' in result:
                combined.append(result['markdown'])
            elif 'text' in result:
                combined.append(result['text'])
            else:
                # Fallback to any available content
                for key in ['html', 'json']:
                    if key in result:
                        combined.append(f"Content in {key} format:\n")
                        combined.append(str(result[key]))
                        break
            
            combined.append("\n")
        
        return "\n".join(combined)

    @classmethod
    def create_with_local_docker(cls, api_url: Optional[str] = None) -> 'WebToTextExtractor':
        """
        Factory method to create a WebToTextExtractor instance configured to use a local Docker instance.
        
        Args:
            api_url (Optional[str]): Custom API URL for the local Docker instance.
                                    If None, will use http://localhost:3002
                                    
        Returns:
            WebToTextExtractor: A new instance configured for local Docker
        """
        return cls(api_key=None, api_url=api_url, use_local_docker=True)
