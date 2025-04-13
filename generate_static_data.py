import json
import os
from datetime import datetime
from db import get_companies, get_company, get_mentions, get_sentiment_stats, get_sentiment_timeline_data

# Ensure the data directory exists
data_dir = os.path.join(os.path.dirname(__file__), 'assets', 'data')
os.makedirs(data_dir, exist_ok=True)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def generate_company_list():
    """Generate a JSON file with the list of all companies"""
    companies = get_companies()
    company_list = [{
        'id': company.id,
        'name': company.name,
        'aliases': company.aliases.split(',') if company.aliases else []
    } for company in companies]
    
    with open(os.path.join(data_dir, 'companies.json'), 'w') as f:
        json.dump(company_list, f, default=json_serial)
    
    print(f"Generated companies.json with {len(company_list)} companies")
    return company_list

def generate_company_data(company_id):
    """Generate JSON data for a specific company"""
    company = get_company(company_id)
    if not company:
        print(f"Company with ID {company_id} not found")
        return
    
    # Get company stats
    stats = get_sentiment_stats(company_id)
    
    # Get company mentions
    mentions = get_mentions(company_id)
    mentions_data = [{
        'id': mention.id,
        'title': mention.title,
        'content': mention.content,
        'sentiment': mention.sentiment,
        'sentiment_score': mention.sentiment_score,
        'url': mention.url,
        'source': mention.source,
        'published_at': mention.published_at
    } for mention in mentions]
    
    # Get timeline data
    timeline_mentions = get_sentiment_timeline_data(company_id)
    timeline_data = [{
        'date': mention.published_at,
        'score': mention.sentiment_score,
        'sentiment': mention.sentiment
    } for mention in timeline_mentions if mention.published_at and mention.sentiment_score]
    
    # Create company data object
    company_data = {
        'company': {
            'id': company.id,
            'name': company.name,
            'aliases': company.aliases.split(',') if company.aliases else []
        },
        'stats': stats,
        'mentions': mentions_data,
        'timeline': timeline_data
    }
    
    # Save to file
    with open(os.path.join(data_dir, f'company_{company_id}.json'), 'w') as f:
        json.dump(company_data, f, default=json_serial)
    
    print(f"Generated data for company: {company.name} (ID: {company_id})")
    return company_data

def generate_all_data():
    """Generate all JSON data files"""
    # Generate company list
    companies = generate_company_list()
    
    # Generate data for each company
    for company in companies:
        generate_company_data(company['id'])
    
    # Generate a combined data file with the first company's data as default
    if companies:
        default_company_data = generate_company_data(companies[0]['id'])
        with open(os.path.join(data_dir, 'dashboard_data.json'), 'w') as f:
            json.dump(default_company_data, f, default=json_serial)
        print(f"Generated dashboard_data.json with default company: {companies[0]['name']}")

if __name__ == "__main__":
    generate_all_data()
    print("Static data generation complete!")