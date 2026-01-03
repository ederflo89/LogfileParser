"""
Example: Using Database Matching in LogfileParser

This example demonstrates how to use the database matching system
to find causes and solutions for log errors.
"""

from core.database_matcher import DatabaseMatcher
from database.turso_client import TursoClient

def main():
    """Main example demonstrating database matching"""
    
    print("=" * 70)
    print("DATABASE MATCHING EXAMPLE")
    print("=" * 70)
    print()
    
    # Step 1: Initialize database client
    print("Step 1: Initialize database client")
    print("-" * 70)
    
    # For this example, we'll use the test database
    db_path = '/tmp/test_sample_db.csv'
    client = TursoClient(database_path=db_path)
    
    print(f"✓ Database loaded: {db_path}")
    entries = client.get_all_entries()
    print(f"✓ Total entries: {len(entries)}")
    print()
    
    # Step 2: Initialize matcher
    print("Step 2: Initialize database matcher")
    print("-" * 70)
    matcher = DatabaseMatcher(client)
    print("✓ Matcher initialized with 3-stage matching:")
    print("  1. Exact Match - Direct comparison")
    print("  2. Normalized Match - Count-prefix + path generalization")
    print("  3. Fuzzy Match - Similarity-based (85%+ threshold)")
    print()
    
    # Step 3: Match various error types
    print("Step 3: Match errors from log files")
    print("-" * 70)
    
    # Simulate errors from log parsing
    log_errors = [
        {
            'text': 'Connection failed',
            'type': '',
            'description': 'From exact database match'
        },
        {
            'text': '17x Connection failed',
            'type': '',
            'description': 'From count-prefix normalization'
        },
        {
            'text': 'Connection has failed',
            'type': '',
            'description': 'From fuzzy matching'
        },
        {
            'text': 'Memory allocation error',
            'type': '',
            'description': 'Exact match for memory error'
        },
        {
            'text': 'Unknown error ABC123',
            'type': '',
            'description': 'Should not match anything'
        }
    ]
    
    for i, error in enumerate(log_errors, 1):
        print(f"\nError {i}: {error['text']}")
        print(f"Context: {error['description']}")
        
        # Perform matching
        result = matcher.match_error(error['text'], error['type'])
        
        if result:
            # Match found
            print(f"  ✓ Match found!")
            print(f"    Type: {result['match_type'].upper()}")
            
            if result['match_type'] == 'fuzzy':
                print(f"    Similarity: {result['similarity']:.1%}")
            
            print(f"    Database entry: \"{result['error_text']}\"")
            print(f"    Cause: {result['cause']}")
            print(f"    Solution: {result['solution']}")
        else:
            # No match
            print(f"  ✗ No match found in database")
    
    print()
    
    # Step 4: Performance check
    print("Step 4: Performance check")
    print("-" * 70)
    import time
    
    test_error = "17x Connection failed"
    iterations = 100
    
    start = time.time()
    for _ in range(iterations):
        matcher.match_error(test_error)
    elapsed = (time.time() - start) * 1000
    
    avg_time = elapsed / iterations
    print(f"✓ Matched {iterations} errors in {elapsed:.2f}ms")
    print(f"✓ Average time per match: {avg_time:.2f}ms")
    print(f"✓ Performance target (<50ms): {'PASS' if avg_time < 50 else 'FAIL'}")
    print()
    
    # Step 5: Cleanup
    print("Step 5: Cleanup")
    print("-" * 70)
    matcher.clear_cache()
    client.close()
    print("✓ Cache cleared")
    print("✓ Database connection closed")
    print()
    
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
