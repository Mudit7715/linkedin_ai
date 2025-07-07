"""
Post Generator Module - Creates algorithm-optimized LinkedIn posts
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from .ollama_connector import OllamaConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostGenerator:
    def __init__(self, ollama_connector: OllamaConnector):
        self.ollama = ollama_connector
        self.post_templates = self._load_post_templates()
        
    def _load_post_templates(self) -> List[Dict[str, str]]:
        """Load proven post templates"""
        return [
            {
                "type": "story",
                "structure": "Hook → Personal story → Lesson → Question"
            },
            {
                "type": "data",
                "structure": "Surprising stat → Context → Insight → Call to action"
            },
            {
                "type": "contrarian",
                "structure": "Common belief → Why it's wrong → Better approach → Discussion"
            },
            {
                "type": "list",
                "structure": "Promise → Numbered list → Elaboration → Engagement"
            }
        ]
    
    def generate_optimized_post(self, 
                              viral_insights: Dict[str, Any],
                              personal_brand: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate an algorithm-optimized post based on viral insights"""
        
        # Extract patterns from viral insights
        patterns = viral_insights.get('patterns', {})
        top_posts = viral_insights.get('top_posts', [])
        common_hashtags = patterns.get('common_hashtags', {})
        
        # Build enhanced prompt with insights
        enhanced_prompt = self._build_enhanced_prompt(
            patterns, top_posts, common_hashtags, personal_brand
        )
        
        # Generate post
        generated_post = self.ollama.generate(
            'viral_post',
            {'viral_insights': json.dumps(viral_insights)},
            custom_prompt=enhanced_prompt
        )
        
        if not generated_post:
            return None
            
        # Post-process for optimization
        optimized_post = self._optimize_post(generated_post, common_hashtags)
        
        # Analyze post quality
        quality_score = self._analyze_post_quality(optimized_post)
        
        return {
            'content': optimized_post,
            'quality_score': quality_score,
            'recommended_time': self._get_optimal_posting_time(),
            'hashtags': self._extract_hashtags(optimized_post),
            'char_count': len(optimized_post),
            'estimated_reach': self._estimate_reach(quality_score)
        }
    
    def _build_enhanced_prompt(self, patterns, top_posts, hashtags, personal_brand):
        """Build an enhanced prompt with all insights"""
        
        prompt = f"""Create a viral LinkedIn post about AI/ML that follows these proven patterns:

VIRAL PATTERNS OBSERVED:
{json.dumps(patterns.get('content_patterns', []), indent=2)}

TOP PERFORMING POSTS STYLE:
- Average length: {patterns.get('avg_content_length', 800)} characters
- Engagement rate: {patterns.get('avg_engagement_rate', 0.05):.1%}

SUCCESSFUL ELEMENTS TO INCLUDE:
1. Strong emotional hook in first line
2. Personal story or contrarian view
3. Specific data point or surprising fact
4. Clear value proposition
5. Question or call-to-action at end

HASHTAGS TO CONSIDER: {', '.join(list(hashtags.keys())[:5])}

PERSONAL BRAND VOICE:
{json.dumps(personal_brand or {'tone': 'professional yet approachable', 'expertise': 'AI/ML student and enthusiast'}, indent=2)}

CONSTRAINTS:
- Maximum 1300 characters
- Use 3-5 relevant hashtags
- Include line breaks for readability
- Start with attention-grabbing first line
- End with engagement driver

Now create a post that will resonate with the AI/ML community on LinkedIn."""
        
        return prompt
    
    def _optimize_post(self, post: str, trending_hashtags: Dict[str, int]) -> str:
        """Optimize post for LinkedIn algorithm"""
        
        # Ensure proper line breaks
        post = self._add_strategic_line_breaks(post)
        
        # Optimize hashtags
        post = self._optimize_hashtags(post, trending_hashtags)
        
        # Ensure hook is strong
        post = self._strengthen_hook(post)
        
        # Add emoji if appropriate
        post = self._add_strategic_emojis(post)
        
        return post.strip()
    
    def _add_strategic_line_breaks(self, post: str) -> str:
        """Add line breaks for readability"""
        sentences = post.split('. ')
        
        optimized = []
        current_paragraph = []
        
        for sentence in sentences:
            current_paragraph.append(sentence)
            
            # Break after 2-3 sentences or at natural breaks
            if len(current_paragraph) >= 2 or any(keyword in sentence.lower() for keyword in ['but', 'however', 'here\'s']):
                optimized.append('. '.join(current_paragraph) + '.')
                optimized.append('')  # Empty line
                current_paragraph = []
        
        if current_paragraph:
            optimized.append('. '.join(current_paragraph))
            
        return '\n'.join(optimized)
    
    def _optimize_hashtags(self, post: str, trending_hashtags: Dict[str, int]) -> str:
        """Optimize hashtags based on trending data"""
        
        # Extract existing hashtags
        existing_hashtags = re.findall(r'#\w+', post)
        
        # If not enough hashtags, add trending ones
        if len(existing_hashtags) < 3:
            top_trending = sorted(trending_hashtags.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for hashtag, _ in top_trending:
                if hashtag not in post and len(existing_hashtags) < 5:
                    post += f' {hashtag}'
                    existing_hashtags.append(hashtag)
                    
        return post
    
    def _strengthen_hook(self, post: str) -> str:
        """Ensure the first line is attention-grabbing"""
        
        lines = post.split('\n')
        first_line = lines[0] if lines else ""
        
        # Check if hook is strong enough
        hook_keywords = ['unpopular opinion', 'breaking', 'just discovered', 
                        'warning', 'stop', 'nobody talks about', 'secret']
        
        if not any(keyword in first_line.lower() for keyword in hook_keywords):
            # Suggest stronger hooks based on content
            if 'learned' in post.lower():
                lines[0] = "🚨 The AI lesson that changed everything for me:"
            elif 'mistake' in post.lower():
                lines[0] = "My biggest AI mistake (so you don't make it):"
            elif any(stat in post for stat in ['%', 'percent', 'million', 'billion']):
                lines[0] = "This AI statistic will blow your mind:"
                
        return '\n'.join(lines)
    
    def _add_strategic_emojis(self, post: str) -> str:
        """Add emojis strategically without overdoing it"""
        
        emoji_map = {
            'ai': '🤖',
            'learning': '📚',
            'idea': '💡',
            'growth': '📈',
            'warning': '⚠️',
            'important': '🔴',
            'success': '✅',
            'failure': '❌',
            'money': '💰',
            'time': '⏰'
        }
        
        # Add maximum 3 emojis
        emoji_count = 0
        for keyword, emoji in emoji_map.items():
            if keyword in post.lower() and emoji not in post and emoji_count < 3:
                post = post.replace(keyword, f'{emoji} {keyword}', 1)
                emoji_count += 1
                
        return post
    
    def _extract_hashtags(self, post: str) -> List[str]:
        """Extract all hashtags from post"""
        return re.findall(r'#\w+', post)
    
    def _analyze_post_quality(self, post: str) -> float:
        """Analyze post quality and return score 0-1"""
        
        score = 0.0
        
        # Length check (optimal: 600-1200 chars)
        length = len(post)
        if 600 <= length <= 1200:
            score += 0.2
        elif 400 <= length <= 1300:
            score += 0.1
            
        # Hook strength
        first_line = post.split('\n')[0]
        if len(first_line) < 100 and any(char in first_line for char in ['?', '!', '🔥', '⚡', '🚨']):
            score += 0.2
            
        # Hashtag presence
        hashtags = self._extract_hashtags(post)
        if 3 <= len(hashtags) <= 5:
            score += 0.1
            
        # Readability (line breaks)
        if post.count('\n') >= 3:
            score += 0.1
            
        # Engagement drivers
        if '?' in post[-50:]:  # Question at end
            score += 0.1
            
        if any(cta in post.lower() for cta in ['comment below', 'what do you think', 'share your', 'let me know']):
            score += 0.1
            
        # Personal element
        if any(personal in post.lower() for personal in ['i learned', 'my experience', 'i discovered', 'i realized']):
            score += 0.1
            
        # Data/credibility
        if any(char in post for char in ['%', '$']) or any(num in post for num in ['study', 'research', 'survey']):
            score += 0.1
            
        return min(score, 1.0)
    
    def _get_optimal_posting_time(self) -> str:
        """Get optimal posting time based on data"""
        
        # LinkedIn optimal times (simplified)
        weekday = datetime.now().weekday()
        
        if weekday < 5:  # Weekday
            return "7:30 AM - 8:30 AM or 5:00 PM - 6:00 PM"
        else:  # Weekend
            return "10:00 AM - 11:00 AM"
            
    def _estimate_reach(self, quality_score: float) -> str:
        """Estimate potential reach based on quality score"""
        
        if quality_score >= 0.8:
            return "High (1000+ impressions likely)"
        elif quality_score >= 0.6:
            return "Medium (500-1000 impressions expected)"
        else:
            return "Low (Under 500 impressions)"
    
    def regenerate_with_feedback(self, original_post: str, feedback: str) -> Dict[str, Any]:
        """Regenerate post based on user feedback"""
        
        prompt = f"""Improve this LinkedIn post based on the feedback:

ORIGINAL POST:
{original_post}

FEEDBACK:
{feedback}

Generate an improved version that addresses the feedback while maintaining viral potential."""
        
        improved_post = self.ollama.generate(
            'viral_post',
            {},
            custom_prompt=prompt
        )
        
        if improved_post:
            return self.generate_optimized_post(
                {'improved': True, 'original': original_post},
                None
            )
            
        return None
