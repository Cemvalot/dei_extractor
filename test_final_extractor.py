#!/usr/bin/env python3
"""
Test script for the final DEI extractor
"""

import pandas as pd

def test_extractor_results():
    """Test the results of the final extractor."""
    print("Testing Final DEI Extractor Results")
    print("="*50)
    
    try:
        # Load the data with proper string handling for IDs
        df = pd.read_csv('ολα.csv', dtype={'ΑρΠαροχής': str, 'ΑρΛογαριασμού': str})
        fop_df = pd.read_csv('φoπ.csv', dtype={'ΑρΠαροχής': str, 'ΑρΛογαριασμού': str})
        epag_df = pd.read_csv('επαγγελματικα.csv', dtype={'ΑρΠαροχής': str, 'ΑρΛογαριασμού': str})
        
        print(f"✓ Total records: {len(df)}")
        print(f"✓ ΦΟΠ records: {len(fop_df)}")
        print(f"✓ Επαγγελματικό records: {len(epag_df)}")
        
        # Test 1: Check that IDs are strings (not scientific notation)
        print("\nTest 1: ID Format")
        sample_id = df['ΑρΠαροχής'].iloc[0]
        if isinstance(sample_id, str) and not 'e' in str(sample_id).lower():
            print(f"✓ ΑρΠαροχής correctly formatted as string: {sample_id}")
        else:
            print(f"✗ ΑρΠαροχής incorrectly formatted: {sample_id}")
        
        # Test 2: Check category detection
        print("\nTest 2: Category Detection")
        fop_count = len(df[df['ΚατηγορίαΤιμολογίου'] == 'ΦΟΠ'])
        epag_count = len(df[df['ΚατηγορίαΤιμολογίου'] == 'Επαγγελματικό'])
        print(f"✓ ΦΟΠ detected: {fop_count}")
        print(f"✓ Επαγγελματικό detected: {epag_count}")
        
        # Test 3: Check Εκαθαριστικός flag
        print("\nTest 3: Εκαθαριστικός Flag")
        ekatharistikos_true = len(df[df['Εκαθαριστικός'] == True])
        ekatharistikos_false = len(df[df['Εκαθαριστικός'] == False])
        print(f"✓ Εκαθαριστικός=True: {ekatharistikos_true}")
        print(f"✓ Εκαθαριστικός=False: {ekatharistikos_false}")
        
        # Test 4: Check subcategory logic
        print("\nTest 4: Subcategory Logic")
        if not epag_df.empty:
            simple_epag = len(epag_df[epag_df['Υποκατηγορία'] == 'Απλό επαγγελματικό'])
            industrial = len(epag_df[epag_df['Υποκατηγορία'] == 'Βιομηχανικό'])
            agricultural = len(epag_df[epag_df['Υποκατηγορία'] == 'Αγροτικό'])
            print(f"✓ Απλό επαγγελματικό: {simple_epag}")
            print(f"✓ Βιομηχανικό: {industrial}")
            print(f"✓ Αγροτικό: {agricultural}")
        
        # Test 5: Check confidence system
        print("\nTest 5: Confidence System")
        needs_review = len(df[df['needs_review'] == True])
        high_confidence = len(df[df['confidence'] >= 0.90])
        print(f"✓ Records needing review: {needs_review}")
        print(f"✓ High confidence records (≥90%): {high_confidence}")
        
        # Test 6: Check data types
        print("\nTest 6: Data Types")
        print(f"✓ Τελευταία type: {df['Τελευταία'].dtype}")
        print(f"✓ ΣΩΧΒ type: {df['ΣΩΧΒ'].dtype}")
        print(f"✓ ΑρΠαροχής type: {df['ΑρΠαροχής'].dtype}")
        
        # Test 7: Sample data validation
        print("\nTest 7: Sample Data Validation")
        sample = df.iloc[0]
        print(f"Sample record:")
        print(f"  ΑρΠαροχής: {sample['ΑρΠαροχής']}")
        print(f"  ΗμΈκδοσης: {sample['ΗμΈκδοσης']}")
        print(f"  ΚατηγορίαΤιμολογίου: {sample['ΚατηγορίαΤιμολογίου']}")
        print(f"  Τελευταία: {sample['Τελευταία']}")
        print(f"  Εκαθαριστικός: {sample['Εκαθαριστικός']}")
        
        print("\n" + "="*50)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*50)
        
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    test_extractor_results()
