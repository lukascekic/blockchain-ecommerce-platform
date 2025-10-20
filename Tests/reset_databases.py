#!/usr/bin/env python3
"""
Skripta za resetovanje baza podataka pre pokretanja testova.
Poziva se automatski iz Tests kontejnera.
"""

import pymysql
import time
import sys

def wait_for_db(host, user, password, max_retries=30):
    """Čeka da MySQL bude dostupan"""
    for i in range(max_retries):
        try:
            conn = pymysql.connect(host=host, user=user, password=password)
            conn.close()
            print(f"[OK] MySQL na {host} je dostupan!")
            return True
        except pymysql.err.OperationalError:
            if i < max_retries - 1:
                print(f"[{i+1}/{max_retries}] Čekam da MySQL na {host} postane dostupan...")
                time.sleep(1)
            else:
                print(f"[ERROR] MySQL na {host} nije dostupan nakon {max_retries} pokušaja!")
                return False
    return False

def reset_database(host, user, password, database_name):
    """Briše i ponovo kreira bazu podataka"""
    try:
        print(f"\n[RESET] Resetujem {database_name} bazu na {host}...")

        # Konektuj se na MySQL server (ne na specifičnu bazu)
        conn = pymysql.connect(host=host, user=user, password=password)
        cursor = conn.cursor()

        # Obriši bazu ako postoji
        cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
        print(f"  [1/2] Obrisana stara {database_name} baza")

        # Kreiraj novu praznu bazu
        cursor.execute(f"CREATE DATABASE {database_name}")
        print(f"  [2/2] Kreirana nova {database_name} baza")

        cursor.close()
        conn.close()

        print(f"[OK] {database_name} baza resetovana!")
        return True

    except Exception as e:
        print(f"[ERROR] Greška pri resetovanju {database_name}: {e}")
        return False

def main():
    print("=" * 60)
    print("  RESETOVANJE BAZA PODATAKA PRE TESTOVA")
    print("=" * 60)

    # Konfiguracija
    auth_db_config = {
        'host': 'authenticationDB',
        'user': 'root',
        'password': 'root',
        'database_name': 'authentication'
    }

    store_db_config = {
        'host': 'storeDB',
        'user': 'root',
        'password': 'root',
        'database_name': 'store'
    }

    # Čekaj da baze budu dostupne
    print("\n[STEP 1/3] Čekam da MySQL serveri postanu dostupni...\n")
    auth_ready = wait_for_db(auth_db_config['host'], auth_db_config['user'], auth_db_config['password'])
    store_ready = wait_for_db(store_db_config['host'], store_db_config['user'], store_db_config['password'])

    if not (auth_ready and store_ready):
        print("\n[ERROR] MySQL serveri nisu dostupni!")
        sys.exit(1)

    # Resetuj authentication bazu
    print("\n[STEP 2/3] Resetujem authentication bazu...")
    if not reset_database(**auth_db_config):
        sys.exit(1)

    # Resetuj store bazu
    print("\n[STEP 3/3] Resetujem store bazu...")
    if not reset_database(**store_db_config):
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  ✓ SVE BAZE SU RESETOVANE - SPREMNO ZA TESTOVE!")
    print("=" * 60)
    print("")

if __name__ == "__main__":
    main()
