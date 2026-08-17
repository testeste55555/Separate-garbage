#!/usr/bin/env python3
"""Deprecated compatibility entrypoint for the non-destructive v1.2 migrator."""

from migrate_schema_v12 import main


if __name__ == "__main__":
    print("NOTICE: Schema v1.1 migrator is retired; running Schema v1.2 migration")
    main()
