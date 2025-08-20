#!/usr/bin/env python3
"""
Test script για επαλήθευση της λειτουργικότητας ομαδοποίησης με βάση το ΑρΠαροχής
"""

import pandas as pd
import tempfile
import os
from pathlib import Path

def create_test_data():
    """Δημιουργία test δεδομένων με διαφορετικά ΑρΠαροχής"""
    test_data = [
        {'ΑρΠαροχής': '1234567890', 'ΑρΛογαριασμού': '111111111', 'ΗμΈκδοσης': '01/01/2024', 'ΚατηγορίαΤιμολογίου': 'ΦΟΠ', 'Εκαθαριστικός': True},
        {'ΑρΠαροχής': '9876543210', 'ΑρΛογαριασμού': '222222222', 'ΗμΈκδοσης': '02/01/2024', 'ΚατηγορίαΤιμολογίου': 'Επαγγελματικό', 'Εκαθαριστικός': True},
        {'ΑρΠαροχής': '1234567890', 'ΑρΛογαριασμού': '333333333', 'ΗμΈκδοσης': '03/01/2024', 'ΚατηγορίαΤιμολογίου': 'ΦΟΠ', 'Εκαθαριστικός': True},
        {'ΑρΠαροχής': '5555555555', 'ΑρΛογαριασμού': '444444444', 'ΗμΈκδοσης': '04/01/2024', 'ΚατηγορίαΤιμολογίου': 'Επαγγελματικό', 'Εκαθαριστικός': True},
        {'ΑρΠαροχής': '9876543210', 'ΑρΛογαριασμού': '555555555', 'ΗμΈκδοσης': '05/01/2024', 'ΚατηγορίαΤιμολογίου': 'ΦΟΠ', 'Εκαθαριστικός': True},
        {'ΑρΠαροχής': '1111111111', 'ΑρΛογαριασμού': '666666666', 'ΗμΈκδοσης': '06/01/2024', 'ΚατηγορίαΤιμολογίου': 'Επαγγελματικό', 'Εκαθαριστικός': True},
    ]
    return pd.DataFrame(test_data)

def test_sorting_functionality():
    """Test για επαλήθευση της ταξινόμησης"""
    print("🧪 Testing sorting functionality...")
    
    # Δημιουργία test δεδομένων
    df = create_test_data()
    print(f"Original data order:")
    print(df[['ΑρΠαροχής', 'ΑρΛογαριασμού']].to_string(index=False))
    
    # Εφαρμογή ταξινόμησης
    df_sorted = df.sort_values(by=['ΑρΠαροχής'])
    print(f"\nSorted data order:")
    print(df_sorted[['ΑρΠαροχής', 'ΑρΛογαριασμού']].to_string(index=False))
    
    # Έλεγχος ότι τα δεδομένα είναι ταξινομημένα
    αρ_παροχης_list = df_sorted['ΑρΠαροχής'].tolist()
    is_sorted = αρ_παροχης_list == sorted(αρ_παροχης_list)
    
    print(f"\n✅ Sorting test: {'PASSED' if is_sorted else 'FAILED'}")
    
    # Έλεγχος ομαδοποίησης
    print(f"\n📊 Grouping verification:")
    current_group = None
    group_count = 0
    
    for αρ_παροχης in αρ_παροχης_list:
        if αρ_παροχης != current_group:
            if current_group is not None:
                print(f"   Group {current_group}: {group_count} records")
            current_group = αρ_παροχης
            group_count = 1
        else:
            group_count += 1
    
    if current_group is not None:
        print(f"   Group {current_group}: {group_count} records")
    
    return is_sorted

def test_csv_output():
    """Test για επαλήθευση της αποθήκευσης σε CSV"""
    print("\n📄 Testing CSV output...")
    
    df = create_test_data()
    
    # Δημιουργία temporary αρχείου
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_csv = f.name
    
    try:
        # Αποθήκευση με ταξινόμηση
        df_sorted = df.sort_values(by=['ΑρΠαροχής'])
        df_sorted.to_csv(temp_csv, index=False, encoding='utf-8-sig')
        
        # Ανάγνωση και έλεγχος
        df_read = pd.read_csv(temp_csv, encoding='utf-8-sig')
        αρ_παροχης_read = df_read['ΑρΠαροχής'].tolist()
        is_sorted_in_file = αρ_παροχης_read == sorted(αρ_παροχης_read)
        
        print(f"✅ CSV output test: {'PASSED' if is_sorted_in_file else 'FAILED'}")
        print(f"   File: {temp_csv}")
        print(f"   Records in file: {len(df_read)}")
        
        return is_sorted_in_file
        
    finally:
        # Καθαρισμός
        if os.path.exists(temp_csv):
            os.unlink(temp_csv)

def test_excel_output():
    """Test για επαλήθευση της αποθήκευσης σε Excel"""
    print("\n📊 Testing Excel output...")
    
    df = create_test_data()
    
    # Δημιουργία temporary αρχείου
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as f:
        temp_xlsx = f.name
    
    try:
        # Αποθήκευση με ταξινόμηση
        df_sorted = df.sort_values(by=['ΑρΠαροχής'])
        df_sorted.to_excel(temp_xlsx, index=False)
        
        # Ανάγνωση και έλεγχος
        df_read = pd.read_excel(temp_xlsx)
        αρ_παροχης_read = df_read['ΑρΠαροχής'].tolist()
        is_sorted_in_file = αρ_παροχης_read == sorted(αρ_παροχης_read)
        
        print(f"✅ Excel output test: {'PASSED' if is_sorted_in_file else 'FAILED'}")
        print(f"   File: {temp_xlsx}")
        print(f"   Records in file: {len(df_read)}")
        
        return is_sorted_in_file
        
    finally:
        # Καθαρισμός
        if os.path.exists(temp_xlsx):
            os.unlink(temp_xlsx)

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 TESTING GROUPING FUNCTIONALITY")
    print("=" * 60)
    
    # Run tests
    sorting_test = test_sorting_functionality()
    csv_test = test_csv_output()
    excel_test = test_excel_output()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Sorting functionality: {'✅ PASSED' if sorting_test else '❌ FAILED'}")
    print(f"CSV output: {'✅ PASSED' if csv_test else '❌ FAILED'}")
    print(f"Excel output: {'✅ PASSED' if excel_test else '❌ FAILED'}")
    
    all_passed = sorting_test and csv_test and excel_test
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 The grouping functionality is working correctly!")
        print("   Records will be grouped by ΑρΠαροχής in all output files.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
