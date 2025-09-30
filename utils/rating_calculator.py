"""
Rating calculation utilities matching backend logic.
"""

from typing import Optional, Tuple


class RatingCalculator:
    """
    Helper class for rating calculations matching backend logic.
    
    Backend formula:
    - avg_rating = SUM(all approved review ratings) / COUNT(approved reviews)
    - reviews_count = COUNT(approved reviews)
    - If no reviews: avg_rating = 0.0, reviews_count = 0
    """
    
    @staticmethod
    def calculate_new_rating(
        current_avg: Optional[float],
        current_count: int,
        new_rating: int
    ) -> Tuple[float, int]:
        """
        Calculate new average rating after adding a review.
        
        Args:
            current_avg: Current average rating (None or 0.0 if no reviews)
            current_count: Current number of reviews
            new_rating: Rating of the new review (1-5)
            
        Returns:
            Tuple of (new_average_rating, new_review_count)
        """
        # Handle edge cases
        if current_count == 0 or current_avg is None or current_avg == 0.0:
            # First review
            return float(new_rating), 1
        
        # Calculate sum of existing ratings
        sum_of_existing = current_avg * current_count
        
        # Add new rating
        new_sum = sum_of_existing + new_rating
        new_count = current_count + 1
        
        # Calculate new average
        new_avg = new_sum / new_count
        
        return round(new_avg, 2), new_count
    
    @staticmethod
    def verify_rating_change(
        initial_avg: Optional[float],
        initial_count: int,
        new_rating: int,
        final_avg: float,
        final_count: int,
        tolerance: float = 0.01
    ) -> Tuple[bool, str]:
        """
        Verify if rating change is mathematically correct.
        
        Args:
            initial_avg: Initial average rating
            initial_count: Initial review count
            new_rating: Rating that was added
            final_avg: Final average rating after adding review
            final_count: Final review count
            tolerance: Acceptable floating point difference
            
        Returns:
            Tuple of (is_correct, explanation)
        """
        expected_avg, expected_count = RatingCalculator.calculate_new_rating(
            initial_avg, initial_count, new_rating
        )
        
        # Check count
        if final_count != expected_count:
            return False, f"Count mismatch: expected {expected_count}, got {final_count}"
        
        # Check average rating with tolerance
        difference = abs(final_avg - expected_avg)
        
        if difference <= tolerance:
            # Within tolerance - consider it correct
            if difference > 0.01:
                # Notable difference but within tolerance
                explanation = f"Rating updated with minor rounding: {initial_avg or 0:.2f} -> {final_avg:.2f} "
                explanation += f"(exact: {expected_avg:.3f}, difference: {difference:.3f})"
            else:
                # Very close match
                explanation = f"Rating correctly updated: {initial_avg or 0:.2f} -> {final_avg:.2f}"
            return True, explanation
        else:
            # Outside tolerance
            explanation = f"Rating mismatch: expected {expected_avg:.2f}, got {final_avg:.2f}\n"
            explanation += f"Calculation: ({initial_avg or 0:.2f} * {initial_count} + {new_rating}) / {expected_count} = {expected_avg:.2f}"
            return False, explanation
    
    @staticmethod
    def get_expected_impact(
        current_avg: Optional[float],
        current_count: int,
        new_rating: int
    ) -> str:
        """
        Get a description of expected impact of adding a review.
        
        Args:
            current_avg: Current average rating
            current_count: Current number of reviews
            new_rating: Rating to be added
            
        Returns:
            Description of expected impact
        """
        if current_count == 0 or current_avg is None or current_avg == 0.0:
            return f"First review will set rating to {new_rating:.1f}"
        
        new_avg, _ = RatingCalculator.calculate_new_rating(current_avg, current_count, new_rating)
        
        if new_avg > current_avg:
            change = new_avg - current_avg
            return f"Rating will increase by {change:.2f} (from {current_avg:.2f} to {new_avg:.2f})"
        elif new_avg < current_avg:
            change = current_avg - new_avg
            return f"Rating will decrease by {change:.2f} (from {current_avg:.2f} to {new_avg:.2f})"
        else:
            return f"Rating will remain {current_avg:.2f}"
