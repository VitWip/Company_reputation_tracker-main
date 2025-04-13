#!/usr/bin/env python
"""
Main runner script for the Company Reputation Tracker.
This script runs the reputation tracking pipeline for companies.
"""

import argparse
import json
from datetime import datetime
import db  # Import db instead of database
from api_client import NewsClient, analyze_mentions  # Adjust import to match your filename
from logger import get_logger, log_function_call, log_info, log_error, log_warning, log_startup, log_shutdown

# Get logger
logger = get_logger()

@log_function_call
def process_company(company_id, article_limit=10):
    """Process a single company.
    
    Args:
        company_id: ID of the company to process
        article_limit: Maximum number of articles to process (default: 10)
    """
    # Get company data
    company = db.get_company(company_id)
    if not company:
        log_error(f"Company with ID {company_id} not found.")
        return None
    
    log_info(f"Processing company: {company.name} (ID: {company.id})")
    
    # Get company aliases
    aliases = db.get_company_aliases(company_id)
    
    # 1. Fetch mentions
    news_client = NewsClient()
    try:
        mentions = news_client.fetch_mentions(company.name, aliases, limit=article_limit)
        log_info(f"Found {len(mentions)} mentions for {company.name}")
        
        if not mentions:
            return {
                "company_name": company.name,
                "company_id": company.id,
                "mentions_added": 0,
                "status": "success",
                "message": "No new mentions found."
            }
    except Exception as e:
        log_error(f"Error fetching mentions: {str(e)}", exc_info=True)
        return {
            "company_name": company.name,
            "company_id": company.id,
            "status": "error",
            "message": f"Error fetching mentions: {str(e)}"
        }
    
    # 2. Analyze sentiment
    try:
        enriched_mentions = analyze_mentions(mentions)
        log_info(f"Completed sentiment analysis for {len(enriched_mentions)} mentions")
    except Exception as e:
        log_error(f"Error analyzing sentiment: {str(e)}", exc_info=True)
        return {
            "company_name": company.name,
            "company_id": company.id,
            "status": "error",
            "message": f"Error analyzing sentiment: {str(e)}"
        }
    
    # 3. Save to database
    try:
        mentions_added = db.add_mentions(company_id, enriched_mentions)
        log_info(f"Added {mentions_added} mentions to the database")
    except Exception as e:
        log_error(f"Error saving mentions: {str(e)}", exc_info=True)
        return {
            "company_name": company.name,
            "company_id": company.id,
            "status": "error",
            "message": f"Error saving mentions: {str(e)}"
        }
    
    # 4. Get updated stats
    stats = db.get_sentiment_stats(company_id)
    
    # Return summary
    return {
        "company_name": company.name,
        "company_id": company.id,
        "mentions_added": mentions_added,
        "status": "success",
        "stats": stats
    }

def run_all_companies(article_limit=10):
    """Process all companies in the database."""
    # Initialize database
    db.init_db()
    
    # Get all companies
    companies = db.get_companies()
    if not companies:
        print("No companies found in the database.")
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "warning",
            "message": "No companies found in the database."
        }
    
    results = []
    for company in companies:
        result = process_company(company.id, article_limit)
        results.append(result)
    
    # Generate summary
    successful = sum(1 for r in results if r and r.get("status") == "success")
    total_mentions = sum(r.get("mentions_added", 0) for r in results if r and r.get("status") == "success")
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "companies_processed": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "total_new_mentions": total_mentions,
        "details": results
    }
    
    # Save summary to file
    with open("pipeline_run_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"Pipeline completed. Processed {len(results)} companies, added {total_mentions} new mentions.")
    return summary

def add_new_company(name, aliases):
    """Add a new company to track."""
    # Initialize database
    db.init_db()
    
    company = db.add_company(name, aliases)
    if company:
        print(f"Added company: {name} (ID: {company.id})")
        return company.id
    else:
        print(f"Failed to add company: {name}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Company Reputation Tracker")
    parser.add_argument("--company", type=int, help="Company ID to process")
    parser.add_argument("--all", action="store_true", help="Process all companies")
    parser.add_argument("--add", action="store_true", help="Add a new company")
    parser.add_argument("--name", type=str, help="Company name (for --add)")
    parser.add_argument("--aliases", type=str, help="Company aliases, comma-separated (for --add)")
    parser.add_argument("--limit", type=int, default=10, help="Limit the number of articles to process (default: 10)")
    
    args = parser.parse_args()
    
    if args.add:
        if not args.name:
            print("Error: --name is required when adding a company")
        else:
            aliases = args.aliases.split(",") if args.aliases else []
            add_new_company(args.name, aliases)
    
    elif args.company:
        result = process_company(args.company, args.limit)
        print(json.dumps(result, indent=2))
    
    elif args.all:
        run_all_companies(args.limit)
    
    else:
        # List all companies
        db.init_db()
        companies = db.get_companies()
        
        if companies:
            print("Available companies:")
            for company in companies:
                aliases = company.aliases.split(",") if company.aliases else []
                print(f"  ID {company.id}: {company.name} (Aliases: {', '.join(aliases)})")
            print("\nUse --company ID to process a specific company")
            print("Use --all to process all companies")
            print("Use --limit N to limit the number of articles (default: 10)")
        else:
            print("No companies found. Add a company with --add --name COMPANY_NAME")