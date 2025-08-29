#!/usr/bin/env python3
"""
Test script to show how the 60-day cutoff changes day by day
"""

from datetime import datetime, timedelta

def show_60_day_progression():
    print("=" * 60)
    print("60-DAY CUTOFF PROGRESSION")
    print("=" * 60)
    
    base_date = datetime.now()
    
    for days_forward in range(0, 5):
        current_date = base_date + timedelta(days=days_forward)
        sixty_days_ago = current_date - timedelta(days=60)
        
        print(f"Date: {current_date.strftime('%Y-%m-%d')} | 60 days ago: {sixty_days_ago.strftime('%Y-%m-%d')}")
    
    print("\nAs you can see, the cutoff date advances by 1 day each day!")
    print("Data that's 'just within' the 60-day window today will be")
    print("'just outside' the window tomorrow and get removed.")

if __name__ == "__main__":
    show_60_day_progression()
