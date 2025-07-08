"""
Semantic Validator for MCP Testing

This module provides semantic validation capabilities using LLMs to evaluate
test outputs based on meaning rather than exact matching. This addresses
the challenge of testing MCP systems where outputs may vary in format
but maintain semantic correctness.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import tiktoken
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from pydantic import BaseModel


class ValidationResult(Enum):
    """Possible validation results."""
    PASS = "PASS"
    FAIL = "FAIL"
    UNCLEAR = "UNCLEAR"
    ERROR = "ERROR"


@dataclass
class SemanticCheck:
    """Definition of a semantic validation check."""
    
    name: str
    description: str
    criteria: str
    weight: float = 1.0  # Importance weight for this check
    required: bool = True  # Whether this check must pass


@dataclass
class ValidationRequest:
    """Request for semantic validation."""
    
    output: Any
    expected_criteria: List[SemanticCheck]
    context: Optional[Dict[str, Any]] = None
    test_name: Optional[str] = None


@dataclass
class ValidationResponse:
    """Response from semantic validation."""
    
    overall_result: ValidationResult
    individual_results: Dict[str, ValidationResult]
    explanations: Dict[str, str]
    confidence_scores: Dict[str, float]
    total_cost: float
    validation_time: float


class SemanticValidator:
    """
    Semantic validator that uses LLMs to evaluate test outputs.
    
    This validator can evaluate whether outputs meet semantic criteria
    even when the exact format varies, which is crucial for testing
    MCP systems with non-deterministic behavior.
    """
    
    def __init__(
        self,
        model_provider: str = "openai",
        model_name: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        cost_per_token: float = 0.00003
    ):
        self.model_provider = model_provider.lower()
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cost_per_token = cost_per_token
        
        self.logger = logging.getLogger("testing.semantic_validator")
        
        # Initialize LLM client
        if self.model_provider == "openai":
            self.client = AsyncOpenAI(api_key=api_key)
        elif self.model_provider == "anthropic":
            self.client = AsyncAnthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
        
        # Initialize tokenizer for cost estimation
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    async def validate(self, request: ValidationRequest) -> ValidationResponse:
        """
        Perform semantic validation on test output.
        
        Args:
            request: Validation request with output and criteria
            
        Returns:
            Validation response with results and explanations
        """
        start_time = time.time()
        total_cost = 0.0
        individual_results = {}
        explanations = {}
        confidence_scores = {}
        
        self.logger.info(f"Starting semantic validation for {len(request.expected_criteria)} criteria")
        
        try:
            # Validate each criterion
            for check in request.expected_criteria:
                result, explanation, confidence, cost = await self._validate_single_criterion(
                    request.output, check, request.context, request.test_name
                )
                
                individual_results[check.name] = result
                explanations[check.name] = explanation
                confidence_scores[check.name] = confidence
                total_cost += cost
                
                self.logger.debug(f"Criterion '{check.name}': {result.value} (confidence: {confidence:.2f})")
            
            # Determine overall result
            overall_result = self._calculate_overall_result(
                individual_results, request.expected_criteria
            )
            
            validation_time = time.time() - start_time
            
            response = ValidationResponse(
                overall_result=overall_result,
                individual_results=individual_results,
                explanations=explanations,
                confidence_scores=confidence_scores,
                total_cost=total_cost,
                validation_time=validation_time
            )
            
            self.logger.info(
                f"Validation completed: {overall_result.value} "
                f"(time: {validation_time:.2f}s, cost: ${total_cost:.4f})"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return ValidationResponse(
                overall_result=ValidationResult.ERROR,
                individual_results={check.name: ValidationResult.ERROR for check in request.expected_criteria},
                explanations={check.name: f"Validation error: {str(e)}" for check in request.expected_criteria},
                confidence_scores={check.name: 0.0 for check in request.expected_criteria},
                total_cost=total_cost,
                validation_time=time.time() - start_time
            )
    
    async def _validate_single_criterion(
        self,
        output: Any,
        check: SemanticCheck,
        context: Optional[Dict[str, Any]],
        test_name: Optional[str]
    ) -> tuple[ValidationResult, str, float, float]:
        """Validate a single semantic criterion."""
        
        # Prepare validation prompt
        prompt = self._build_validation_prompt(output, check, context, test_name)
        
        # Get LLM evaluation
        response_text, cost = await self._call_llm(prompt)
        
        # Parse LLM response
        result, explanation, confidence = self._parse_llm_response(response_text, check)
        
        return result, explanation, confidence, cost
    
    def _build_validation_prompt(
        self,
        output: Any,
        check: SemanticCheck,
        context: Optional[Dict[str, Any]],
        test_name: Optional[str]
    ) -> str:
        """Build a validation prompt for the LLM."""
        
        output_str = self._format_output_for_prompt(output)
        context_str = json.dumps(context, indent=2) if context else "No additional context provided."
        
        prompt = f"""You are an expert test validator evaluating the output of an AI agent test.

Test Information:
- Test Name: {test_name or 'Unknown'}
- Check Name: {check.name}
- Check Description: {check.description}

Validation Criteria:
{check.criteria}

Test Output to Evaluate:
{output_str}

Additional Context:
{context_str}

Instructions:
1. Evaluate whether the test output meets the specified criteria
2. Consider the semantic meaning, not just exact text matching
3. Be thorough but fair in your evaluation
4. Provide a clear explanation of your reasoning

Response Format:
Result: [PASS/FAIL/UNCLEAR]
Confidence: [0.0-1.0]
Explanation: [Detailed explanation of your evaluation]

Your evaluation:"""

        return prompt
    
    def _format_output_for_prompt(self, output: Any) -> str:
        """Format test output for inclusion in prompt."""
        if isinstance(output, str):
            return output
        elif isinstance(output, dict):
            return json.dumps(output, indent=2)
        elif hasattr(output, '__dict__'):
            return json.dumps(output.__dict__, indent=2, default=str)
        else:
            return str(output)
    
    async def _call_llm(self, prompt: str) -> tuple[str, float]:
        """Call the LLM with the validation prompt."""
        
        # Estimate tokens for cost calculation
        prompt_tokens = len(self.tokenizer.encode(prompt))
        
        try:
            if self.model_provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                response_text = response.choices[0].message.content
                
                # Calculate actual cost if usage info is available
                if hasattr(response, 'usage'):
                    total_tokens = response.usage.total_tokens
                    cost = total_tokens * self.cost_per_token
                else:
                    # Estimate cost
                    estimated_response_tokens = len(self.tokenizer.encode(response_text or ""))
                    cost = (prompt_tokens + estimated_response_tokens) * self.cost_per_token
                
            elif self.model_provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response_text = response.content[0].text
                
                # Estimate cost for Anthropic (adjust pricing as needed)
                estimated_response_tokens = len(self.tokenizer.encode(response_text))
                cost = (prompt_tokens + estimated_response_tokens) * self.cost_per_token
                
            else:
                raise ValueError(f"Unsupported provider: {self.model_provider}")
            
            return response_text, cost
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_llm_response(
        self,
        response_text: str,
        check: SemanticCheck
    ) -> tuple[ValidationResult, str, float]:
        """Parse the LLM's validation response."""
        
        try:
            lines = response_text.strip().split('\n')
            result = ValidationResult.UNCLEAR
            confidence = 0.5
            explanation = "Could not parse LLM response"
            
            for line in lines:
                line = line.strip()
                if line.startswith("Result:"):
                    result_str = line.split(":", 1)[1].strip().upper()
                    if result_str in [r.value for r in ValidationResult]:
                        result = ValidationResult(result_str)
                
                elif line.startswith("Confidence:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
                    except ValueError:
                        confidence = 0.5
                
                elif line.startswith("Explanation:"):
                    explanation = line.split(":", 1)[1].strip()
            
            # If we couldn't find a structured explanation, use the whole response
            if explanation == "Could not parse LLM response":
                explanation = response_text
            
            return result, explanation, confidence
            
        except Exception as e:
            self.logger.warning(f"Failed to parse LLM response: {e}")
            return ValidationResult.ERROR, f"Parse error: {str(e)}", 0.0
    
    def _calculate_overall_result(
        self,
        individual_results: Dict[str, ValidationResult],
        criteria: List[SemanticCheck]
    ) -> ValidationResult:
        """Calculate overall validation result from individual check results."""
        
        required_checks = [check for check in criteria if check.required]
        optional_checks = [check for check in criteria if not check.required]
        
        # Check required criteria
        required_failures = [
            check for check in required_checks
            if individual_results.get(check.name) == ValidationResult.FAIL
        ]
        
        required_errors = [
            check for check in required_checks
            if individual_results.get(check.name) == ValidationResult.ERROR
        ]
        
        # If any required check failed, overall result is FAIL
        if required_failures:
            return ValidationResult.FAIL
        
        # If any required check had an error, overall result is ERROR
        if required_errors:
            return ValidationResult.ERROR
        
        # Check for any unclear results
        unclear_results = [
            check for check in criteria
            if individual_results.get(check.name) == ValidationResult.UNCLEAR
        ]
        
        if unclear_results:
            return ValidationResult.UNCLEAR
        
        # All checks passed
        return ValidationResult.PASS
    
    async def validate_multiple(
        self,
        requests: List[ValidationRequest]
    ) -> List[ValidationResponse]:
        """Validate multiple requests concurrently."""
        
        self.logger.info(f"Starting batch validation of {len(requests)} requests")
        
        # Execute validations concurrently
        tasks = [self.validate(request) for request in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        final_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                self.logger.error(f"Validation {i} failed: {response}")
                # Create error response
                request = requests[i]
                error_response = ValidationResponse(
                    overall_result=ValidationResult.ERROR,
                    individual_results={
                        check.name: ValidationResult.ERROR 
                        for check in request.expected_criteria
                    },
                    explanations={
                        check.name: f"Validation exception: {str(response)}"
                        for check in request.expected_criteria
                    },
                    confidence_scores={
                        check.name: 0.0 
                        for check in request.expected_criteria
                    },
                    total_cost=0.0,
                    validation_time=0.0
                )
                final_responses.append(error_response)
            else:
                final_responses.append(response)
        
        return final_responses
    
    def create_semantic_check(
        self,
        name: str,
        description: str,
        criteria: str,
        weight: float = 1.0,
        required: bool = True
    ) -> SemanticCheck:
        """Helper method to create semantic checks."""
        return SemanticCheck(
            name=name,
            description=description,
            criteria=criteria,
            weight=weight,
            required=required
        )
    
    def get_cost_estimate(self, prompt: str) -> float:
        """Estimate the cost of validating with the given prompt."""
        prompt_tokens = len(self.tokenizer.encode(prompt))
        estimated_total_tokens = prompt_tokens + self.max_tokens
        return estimated_total_tokens * self.cost_per_token


# Convenience functions for common validation patterns

def create_content_check(expected_content: str, weight: float = 1.0) -> SemanticCheck:
    """Create a check for expected content presence."""
    return SemanticCheck(
        name="content_check",
        description="Verify that expected content is present",
        criteria=f"The output should contain or reference: {expected_content}",
        weight=weight
    )


def create_format_check(expected_format: str, weight: float = 1.0) -> SemanticCheck:
    """Create a check for expected format."""
    return SemanticCheck(
        name="format_check",
        description="Verify that output follows expected format",
        criteria=f"The output should be formatted as: {expected_format}",
        weight=weight
    )


def create_function_call_check(function_name: str, weight: float = 1.0) -> SemanticCheck:
    """Create a check for function call usage."""
    return SemanticCheck(
        name="function_call_check",
        description="Verify that specific function was called",
        criteria=f"The output should indicate that the function '{function_name}' was called or used",
        weight=weight
    )


def create_semantic_condition_check(condition: str, weight: float = 1.0) -> SemanticCheck:
    """Create a check for semantic conditions."""
    return SemanticCheck(
        name="semantic_condition",
        description="Verify that semantic condition is met",
        criteria=condition,
        weight=weight
    ) 