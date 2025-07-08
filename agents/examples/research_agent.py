"""
Research Agent Example

This module demonstrates a concrete implementation of the base agent patterns
for MCP-powered multi-agent systems. The research agent can autonomously
conduct research tasks by:

- Searching for information via MCP tools
- Analyzing and synthesizing findings
- Coordinating with other agents
- Maintaining research context and progress
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from agents.base.agent import BaseAgent, AgentConfig
from coordination.state.context_bundle import ContextBundle


class ResearchAgent(BaseAgent):
    """
    Research agent that demonstrates autonomous research capabilities.
    
    This agent can:
    - Conduct literature searches
    - Analyze research topics
    - Synthesize findings from multiple sources
    - Coordinate with other agents for comprehensive research
    """
    
    async def _initialize_agent(self) -> None:
        """Initialize the research agent with specific capabilities."""
        self.logger.info("Initializing research agent capabilities")
        
        # Initialize research-specific state
        self.research_stack = []  # Stack of research tasks
        self.completed_searches = set()  # Track completed searches to avoid duplicates
        self.findings_database = {}  # Local cache of research findings
        
        # Register agent with coordination system
        await self._update_shared_state("agent_type", "research")
        await self._update_shared_state("capabilities", [
            "web_search",
            "document_analysis", 
            "synthesis",
            "fact_checking",
            "citation_management"
        ])
        
        self.logger.info("Research agent initialization completed")
    
    async def _determine_next_action(self, context: ContextBundle) -> Optional[str]:
        """
        Determine the next research action based on current context.
        
        Args:
            context: Current context bundle with task and coordination info
            
        Returns:
            Next action to take, or None if no action needed
        """
        # Check if there are any pending research requests
        pending_requests = context.get_shared_value("pending_research_requests", [])
        
        if pending_requests:
            # Take the highest priority research request
            request = pending_requests[0]
            return f"conduct_research:{request['topic']}:{request.get('depth', 'basic')}"
        
        # Check if there are research tasks in our stack
        if self.research_stack:
            task = self.research_stack[-1]  # Take from top of stack
            return f"continue_research:{task['topic']}"
        
        # Check if other agents need research support
        other_agents = context.get_active_agents()
        for agent in other_agents:
            if agent.get("needs_research") and agent.get("research_topic"):
                return f"support_research:{agent['research_topic']}"
        
        # Check for autonomous research opportunities
        current_task = context.get_task()
        if "research" in current_task.lower() or "analyze" in current_task.lower():
            return f"autonomous_research:{current_task}"
        
        # No action needed
        return None
    
    async def _execute_task_with_context(
        self, 
        task: str, 
        context: ContextBundle
    ) -> Dict[str, Any]:
        """
        Execute a research task with the provided context.
        
        Args:
            task: Task description
            context: Context bundle with research requirements
            
        Returns:
            Task execution result with research findings
        """
        self.logger.info(f"Executing research task: {task}")
        
        try:
            # Parse task type and parameters
            if task.startswith("conduct_research:"):
                return await self._conduct_research(task, context)
            elif task.startswith("continue_research:"):
                return await self._continue_research(task, context)
            elif task.startswith("support_research:"):
                return await self._support_research(task, context)
            elif task.startswith("autonomous_research:"):
                return await self._autonomous_research(task, context)
            else:
                # Generic research task
                return await self._generic_research(task, context)
                
        except Exception as e:
            self.logger.error(f"Research task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cost": 0.0
            }
    
    async def _conduct_research(self, task: str, context: ContextBundle) -> Dict[str, Any]:
        """Conduct new research on a specific topic."""
        parts = task.split(":")
        topic = parts[1] if len(parts) > 1 else "unknown"
        depth = parts[2] if len(parts) > 2 else "basic"
        
        self.logger.info(f"Starting research on topic: {topic} (depth: {depth})")
        
        # Check if we've already researched this topic
        research_key = f"{topic}:{depth}"
        if research_key in self.completed_searches:
            self.logger.info(f"Research already completed for {research_key}")
            return {
                "success": True,
                "findings": self.findings_database.get(research_key, {}),
                "cost": 0.0,
                "cached": True
            }
        
        total_cost = 0.0
        findings = {}
        
        try:
            # Step 1: Conduct web search
            if context.has_tool("web_search"):
                search_result = await self._call_mcp_tool(
                    "web_search",
                    query=topic,
                    max_results=10 if depth == "deep" else 5
                )
                
                findings["web_search"] = search_result.get("result", {})
                total_cost += search_result.get("cost", 0.1)
            
            # Step 2: Search academic databases if available
            if context.has_tool("academic_search") and depth == "deep":
                academic_result = await self._call_mcp_tool(
                    "academic_search",
                    query=topic,
                    max_results=5
                )
                
                findings["academic_sources"] = academic_result.get("result", {})
                total_cost += academic_result.get("cost", 0.15)
            
            # Step 3: Analyze and synthesize findings
            if context.has_tool("text_analysis"):
                analysis_result = await self._call_mcp_tool(
                    "text_analysis",
                    text=json.dumps(findings),
                    analysis_type="synthesis"
                )
                
                findings["synthesis"] = analysis_result.get("result", {})
                total_cost += analysis_result.get("cost", 0.2)
            
            # Step 4: Fact-check key claims if deep research
            if depth == "deep" and context.has_tool("fact_check"):
                key_claims = self._extract_key_claims(findings)
                for claim in key_claims[:3]:  # Limit to top 3 claims
                    fact_check_result = await self._call_mcp_tool(
                        "fact_check",
                        claim=claim
                    )
                    
                    if "fact_checks" not in findings:
                        findings["fact_checks"] = {}
                    findings["fact_checks"][claim] = fact_check_result.get("result", {})
                    total_cost += fact_check_result.get("cost", 0.1)
            
            # Cache the results
            self.completed_searches.add(research_key)
            self.findings_database[research_key] = findings
            
            # Update shared state with new findings
            await self._update_shared_state(f"research_findings:{topic}", findings)
            
            return {
                "success": True,
                "topic": topic,
                "depth": depth,
                "findings": findings,
                "cost": total_cost,
                "sources_count": len(findings.get("web_search", {}).get("results", [])),
                "cached": False
            }
            
        except Exception as e:
            self.logger.error(f"Research conduct failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cost": total_cost
            }
    
    async def _continue_research(self, task: str, context: ContextBundle) -> Dict[str, Any]:
        """Continue an existing research task."""
        parts = task.split(":")
        topic = parts[1] if len(parts) > 1 else "unknown"
        
        # Find the research task in our stack
        task_info = None
        for i, research_task in enumerate(self.research_stack):
            if research_task["topic"] == topic:
                task_info = research_task
                break
        
        if not task_info:
            return {
                "success": False,
                "error": f"No continuing research found for topic: {topic}",
                "cost": 0.0
            }
        
        # Determine next step based on current progress
        next_step = task_info.get("next_step", "search")
        
        if next_step == "search":
            # Continue with additional searches
            return await self._conduct_additional_search(topic, task_info, context)
        elif next_step == "analysis":
            # Perform deeper analysis
            return await self._perform_analysis(topic, task_info, context)
        elif next_step == "synthesis":
            # Synthesize all findings
            return await self._synthesize_findings(topic, task_info, context)
        else:
            # Complete the research
            self.research_stack.remove(task_info)
            return {
                "success": True,
                "topic": topic,
                "status": "completed",
                "findings": task_info.get("findings", {}),
                "cost": 0.0
            }
    
    async def _support_research(self, task: str, context: ContextBundle) -> Dict[str, Any]:
        """Support another agent's research request."""
        parts = task.split(":")
        topic = parts[1] if len(parts) > 1 else "unknown"
        
        # Check if we have existing research on this topic
        for key, findings in self.findings_database.items():
            if topic.lower() in key.lower():
                # Share our findings
                await self._update_shared_state(f"shared_research:{topic}", findings)
                
                return {
                    "success": True,
                    "topic": topic,
                    "action": "shared_existing_research",
                    "findings": findings,
                    "cost": 0.0
                }
        
        # Conduct quick research to support the other agent
        return await self._conduct_research(f"conduct_research:{topic}:basic", context)
    
    async def _autonomous_research(self, task: str, context: ContextBundle) -> Dict[str, Any]:
        """Conduct autonomous research based on task context."""
        # Extract research topics from the task description
        research_topics = self._extract_research_topics(task)
        
        if not research_topics:
            return {
                "success": False,
                "error": "No research topics identified in task",
                "cost": 0.0
            }
        
        total_cost = 0.0
        all_findings = {}
        
        # Research each identified topic
        for topic in research_topics[:3]:  # Limit to top 3 topics
            result = await self._conduct_research(f"conduct_research:{topic}:basic", context)
            
            if result["success"]:
                all_findings[topic] = result["findings"]
                total_cost += result["cost"]
        
        return {
            "success": True,
            "action": "autonomous_research",
            "topics": research_topics,
            "findings": all_findings,
            "cost": total_cost
        }
    
    async def _generic_research(self, task: str, context: ContextBundle) -> Dict[str, Any]:
        """Handle generic research tasks."""
        # Try to identify research intent in the task
        if any(keyword in task.lower() for keyword in ["search", "find", "research", "investigate"]):
            # Extract the main subject
            topic = self._extract_main_subject(task)
            return await self._conduct_research(f"conduct_research:{topic}:basic", context)
        
        return {
            "success": False,
            "error": f"Unable to determine research action for task: {task}",
            "cost": 0.0
        }
    
    # Helper methods
    
    def _extract_key_claims(self, findings: Dict[str, Any]) -> List[str]:
        """Extract key claims from research findings for fact-checking."""
        claims = []
        
        # Extract from synthesis if available
        synthesis = findings.get("synthesis", {})
        if isinstance(synthesis, dict) and "key_points" in synthesis:
            claims.extend(synthesis["key_points"][:5])
        
        # Extract from web search results
        web_results = findings.get("web_search", {}).get("results", [])
        for result in web_results[:3]:
            if "snippet" in result:
                # Simple extraction - in practice, would use NLP
                sentences = result["snippet"].split(".")
                claims.extend([s.strip() for s in sentences if len(s.strip()) > 20])
        
        return claims[:10]  # Limit to top 10 claims
    
    def _extract_research_topics(self, task: str) -> List[str]:
        """Extract potential research topics from a task description."""
        # Simple keyword-based extraction - in practice, would use NLP
        keywords = []
        
        # Look for common research indicators
        research_indicators = ["about", "regarding", "on", "study", "analyze", "investigate"]
        
        words = task.lower().split()
        for i, word in enumerate(words):
            if word in research_indicators and i + 1 < len(words):
                # Take the next few words as potential topics
                topic_words = words[i+1:i+4]
                topic = " ".join(topic_words)
                keywords.append(topic)
        
        # Also look for capitalized words (likely proper nouns)
        capitalized_words = [word for word in task.split() if word[0].isupper() and len(word) > 2]
        keywords.extend(capitalized_words)
        
        return list(set(keywords))[:5]  # Return unique topics, limit to 5
    
    def _extract_main_subject(self, task: str) -> str:
        """Extract the main subject from a task description."""
        # Simple implementation - in practice, would use NLP
        words = task.split()
        
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        content_words = [word for word in words if word.lower() not in stop_words]
        
        # Take first few content words as the subject
        return " ".join(content_words[:3])
    
    async def _conduct_additional_search(self, topic: str, task_info: Dict, context: ContextBundle) -> Dict[str, Any]:
        """Conduct additional searches for continuing research."""
        # Implementation for additional search steps
        return {
            "success": True,
            "action": "additional_search",
            "topic": topic,
            "cost": 0.1
        }
    
    async def _perform_analysis(self, topic: str, task_info: Dict, context: ContextBundle) -> Dict[str, Any]:
        """Perform deeper analysis on research findings."""
        # Implementation for analysis steps
        return {
            "success": True,
            "action": "analysis",
            "topic": topic,
            "cost": 0.2
        }
    
    async def _synthesize_findings(self, topic: str, task_info: Dict, context: ContextBundle) -> Dict[str, Any]:
        """Synthesize all research findings."""
        # Implementation for synthesis steps
        return {
            "success": True,
            "action": "synthesis",
            "topic": topic,
            "cost": 0.15
        }


# Example usage and configuration
async def create_research_agent(mcp_server_urls: List[str]) -> ResearchAgent:
    """Create and initialize a research agent."""
    config = AgentConfig(
        name="research_agent",
        description="Autonomous research agent capable of conducting comprehensive research tasks",
        mcp_server_urls=mcp_server_urls,
        max_iterations=20,
        sleep_interval=2.0,
        cost_limit=25.0,
        log_level="INFO"
    )
    
    agent = ResearchAgent(config)
    await agent.initialize()
    
    return agent


# Example usage
async def main():
    """Example usage of the research agent."""
    # Example MCP server URLs
    mcp_servers = [
        "http://localhost:8001/mcp",  # Context server
        "http://localhost:8002/mcp",  # Tools server
    ]
    
    # Create and start the research agent
    agent = await create_research_agent(mcp_servers)
    
    try:
        # Execute a research task
        result = await agent.execute_task(
            "Research the current state of artificial intelligence in healthcare",
            context={"priority": "high", "depth": "comprehensive"}
        )
        
        print("Research Results:")
        print(json.dumps(result, indent=2))
        
        # Start autonomous loop for continuous operation
        # await agent.start_autonomous_loop()
        
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main()) 