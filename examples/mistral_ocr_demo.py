#!/usr/bin/env python3
"""
Mistral OCR Annotation MCP Server Demo

This script demonstrates how to use the Mistral OCR MCP server
for processing PDFs and extracting structured annotations.
"""

import asyncio
import sys
import json
import os
from pathlib import Path

# Setup path
current_dir = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, current_dir)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from mcp.client.real_mcp_client import RealMCPClient

console = Console()

class MistralOCRDemo:
    """Demo class for Mistral OCR MCP server."""
    
    def __init__(self):
        self.client = RealMCPClient()
        self.connected = False
        
        # Example PDFs for testing
        self.example_pdfs = {
            "ai_research": "https://arxiv.org/pdf/2310.06825.pdf",
            "attention_paper": "https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf",
            "transformer_paper": "https://arxiv.org/pdf/1706.03762.pdf",
            "bert_paper": "https://arxiv.org/pdf/1810.04805.pdf",
            "gpt_paper": "https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf"
        }
    
    async def connect(self):
        """Connect to the Mistral OCR MCP server."""
        console.print("🔗 Connecting to Mistral OCR MCP server...")
        
        # Check if API key is set
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            console.print("⚠️  [yellow]MISTRAL_API_KEY not found. Server will run in mock mode.[/yellow]")
            console.print("   Set your API key: export MISTRAL_API_KEY='your_key_here'")
            console.print("   Or continue with mock data for testing...")
        
        success = await self.client.connect_to_server(
            "mistral_ocr",
            "python",
            ["mcp/servers/mistral_ocr_server.py"],
            env={"MISTRAL_API_KEY": api_key} if api_key else {}
        )
        
        if success:
            self.connected = True
            console.print("✅ Connected to Mistral OCR MCP server!")
            
            # Show available tools
            tools = await self.client.list_tools("mistral_ocr")
            if tools.get("mistral_ocr"):
                console.print(f"📚 Available tools: {len(tools['mistral_ocr'])}")
                
                table = Table(title="Mistral OCR Tools")
                table.add_column("Tool", style="cyan")
                table.add_column("Description", style="green")
                
                for tool in tools["mistral_ocr"]:
                    table.add_row(tool.name, tool.description or "OCR processing tool")
                
                console.print(table)
        else:
            console.print("❌ Failed to connect to Mistral OCR server")
        
        return success
    
    async def demo_document_annotation(self):
        """Demo document-level annotation extraction."""
        if not self.connected:
            return
        
        console.print("\n📄 Demo 1: Document Annotation")
        
        # Let user choose a PDF
        console.print("Available example PDFs:")
        for key, url in self.example_pdfs.items():
            console.print(f"  {key}: {url}")
        
        pdf_choice = Prompt.ask(
            "Choose PDF",
            choices=list(self.example_pdfs.keys()) + ["custom"],
            default="ai_research"
        )
        
        if pdf_choice == "custom":
            pdf_url = Prompt.ask("Enter PDF URL")
        else:
            pdf_url = self.example_pdfs[pdf_choice]
        
        console.print(f"Processing: {pdf_url}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Extracting document annotations...", total=None)
                
                result = await self.client.call_tool("mistral_ocr", "process_pdf_document_annotation", {
                    "document_url": pdf_url,
                    "pages": "0,1,2,3",  # First 4 pages
                    "include_images": False
                })
                
                progress.update(task, description="Document annotation complete!")
            
            # Parse and display results
            self.display_tool_result("Document Annotation", result)
                
        except Exception as e:
            console.print(f"❌ Document annotation error: {e}")
    
    async def demo_bbox_annotation(self):
        """Demo BBOX annotation extraction."""
        if not self.connected:
            return
        
        console.print("\n📦 Demo 2: BBOX Annotation")
        
        pdf_url = self.example_pdfs["attention_paper"]  # Use attention paper for demo
        console.print(f"Processing: {pdf_url}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Extracting BBOX annotations...", total=None)
                
                result = await self.client.call_tool("mistral_ocr", "process_pdf_bbox_annotation", {
                    "document_url": pdf_url,
                    "pages": "0,1",  # First 2 pages
                    "include_images": False
                })
                
                progress.update(task, description="BBOX annotation complete!")
            
            # Parse and display results
            self.display_tool_result("BBOX Annotation", result)
                
        except Exception as e:
            console.print(f"❌ BBOX annotation error: {e}")
    
    async def demo_full_annotation(self):
        """Demo complete annotation extraction."""
        if not self.connected:
            return
        
        console.print("\n🔍 Demo 3: Full Annotation (Document + BBOX + Images)")
        
        pdf_url = self.example_pdfs["bert_paper"]
        console.print(f"Processing: {pdf_url}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Extracting full annotations...", total=None)
                
                result = await self.client.call_tool("mistral_ocr", "process_pdf_full_annotation", {
                    "document_url": pdf_url,
                    "pages": "0,1"  # First 2 pages only for demo
                })
                
                progress.update(task, description="Full annotation complete!")
            
            # Parse and display results
            self.display_tool_result("Full Annotation", result)
                
        except Exception as e:
            console.print(f"❌ Full annotation error: {e}")
    
    async def demo_research_paper_analysis(self):
        """Demo specialized research paper analysis."""
        if not self.connected:
            return
        
        console.print("\n🔬 Demo 4: Research Paper Analysis")
        
        pdf_url = self.example_pdfs["transformer_paper"]
        console.print(f"Analyzing research paper: {pdf_url}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing research paper...", total=None)
                
                result = await self.client.call_tool("mistral_ocr", "analyze_research_paper", {
                    "document_url": pdf_url
                })
                
                progress.update(task, description="Research paper analysis complete!")
            
            # Parse and display results
            self.display_tool_result("Research Paper Analysis", result)
                
        except Exception as e:
            console.print(f"❌ Research paper analysis error: {e}")
    
    def display_tool_result(self, title: str, result):
        """Display tool call result in a formatted way."""
        console.print(f"\n📊 {title} Results:")
        
        try:
            # Extract content from result
            if hasattr(result, 'content') and result.content:
                content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            else:
                content = str(result)
            
            # Try to parse as JSON for better display
            try:
                data = json.loads(content)
                
                # Display structured data
                if "document_annotation" in data:
                    self.display_document_annotation(data["document_annotation"])
                
                if "bbox_annotations" in data:
                    self.display_bbox_annotations(data["bbox_annotations"])
                
                if "error" in data:
                    console.print(f"❌ Error: {data['error']}")
                
                if "status" in data:
                    console.print(f"Status: {data['status']}")
                
                # Show other fields
                other_fields = {k: v for k, v in data.items() 
                              if k not in ["document_annotation", "bbox_annotations", "error", "status"]}
                
                if other_fields:
                    console.print("\n📋 Additional Information:")
                    for key, value in other_fields.items():
                        if key == "image_base64":
                            console.print(f"  {key}: [included - {len(str(value))} characters]")
                        elif isinstance(value, list):
                            console.print(f"  {key}: {len(value)} items")
                        else:
                            console.print(f"  {key}: {value}")
                            
            except json.JSONDecodeError:
                # If not JSON, display as text
                console.print(content)
                
        except Exception as e:
            console.print(f"❌ Error displaying result: {e}")
            console.print(f"Raw result: {result}")
    
    def display_document_annotation(self, annotation: dict):
        """Display document annotation in a structured format."""
        console.print("\n📄 Document Information:")
        
        table = Table(title="Document Properties")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in annotation.items():
            if isinstance(value, list):
                if key == "chapter_titles":
                    table.add_row(key, f"{len(value)} chapters found")
                elif key == "urls":
                    table.add_row(key, f"{len(value)} URLs found")
                else:
                    table.add_row(key, f"{len(value)} items")
            else:
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."
                table.add_row(key, display_value)
        
        console.print(table)
        
        # Show lists separately
        if annotation.get("chapter_titles"):
            console.print("\n📚 Chapter Titles:")
            for i, title in enumerate(annotation["chapter_titles"], 1):
                console.print(f"  {i}. {title}")
        
        if annotation.get("urls"):
            console.print("\n🔗 URLs Found:")
            for url in annotation["urls"]:
                console.print(f"  • {url}")
    
    def display_bbox_annotations(self, annotations: list):
        """Display BBOX annotations in a structured format."""
        console.print("\n📦 Content Regions:")
        
        table = Table(title="BBOX Annotations")
        table.add_column("#", style="yellow")
        table.add_column("Type", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Summary", style="blue")
        
        for i, bbox in enumerate(annotations, 1):
            summary = bbox.get("summary", "N/A")
            if len(summary) > 50:
                summary = summary[:50] + "..."
                
            table.add_row(
                str(i),
                bbox.get("document_type", "Unknown"),
                bbox.get("short_description", "N/A"),
                summary
            )
        
        console.print(table)
    
    async def run_interactive_demo(self):
        """Run interactive demonstration."""
        console.print(Panel.fit(
            "[bold blue]🤖 Mistral OCR Annotation MCP Demo[/bold blue]\n"
            "Process PDFs and extract structured annotations",
            border_style="blue"
        ))
        
        # Connect to server
        connected = await self.connect()
        
        if not connected:
            console.print("\n[red]❌ Could not connect to Mistral OCR server[/red]")
            console.print("\n[yellow]💡 Setup instructions:[/yellow]")
            console.print("1. Install dependencies: pip install mistralai")
            console.print("2. Set API key: export MISTRAL_API_KEY='your_key_here'")
            console.print("3. Run this demo again")
            return
        
        demos = {
            "1": ("Document Annotation", self.demo_document_annotation),
            "2": ("BBOX Annotation", self.demo_bbox_annotation),
            "3": ("Full Annotation", self.demo_full_annotation),
            "4": ("Research Paper Analysis", self.demo_research_paper_analysis),
            "5": ("Run All Demos", self.run_all_demos)
        }
        
        while True:
            console.print("\n[bold]Available Demos:[/bold]")
            for key, (name, _) in demos.items():
                console.print(f"  {key}. {name}")
            console.print("  0. Exit")
            
            choice = Prompt.ask("\nSelect a demo", choices=list(demos.keys()) + ["0"])
            
            if choice == "0":
                break
            elif choice in demos:
                name, demo_func = demos[choice]
                console.print(f"\n🚀 Running: {name}")
                await demo_func()
                console.print(f"✅ {name} completed!\n")
            
            if not Confirm.ask("Continue with more demos?", default=True):
                break
    
    async def run_all_demos(self):
        """Run all demos in sequence."""
        demos = [
            ("Document Annotation", self.demo_document_annotation),
            ("BBOX Annotation", self.demo_bbox_annotation),
            ("Full Annotation", self.demo_full_annotation),
            ("Research Paper Analysis", self.demo_research_paper_analysis)
        ]
        
        for name, demo_func in demos:
            console.print(f"\n🚀 Running: {name}")
            await demo_func()
            console.print(f"✅ {name} completed!")
            await asyncio.sleep(1)
    
    async def cleanup(self):
        """Clean up connections."""
        await self.client.disconnect_all()

async def main():
    """Run the Mistral OCR demo."""
    demo = MistralOCRDemo()
    
    try:
        await demo.run_interactive_demo()
    except KeyboardInterrupt:
        console.print("\n🛑 Demo interrupted")
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await demo.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 