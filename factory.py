import json
from faker import Factory
from collections import Counter
from collections import MutableMapping
from collections import defaultdict

generator = Factory.create()

def generate_domains(emails):
	"""
	Pass through a list of emails and count domains to whitelist.
	"""
	# Count all the domains in each email address
	counts  = Counter([
		email.split("@")[-1] for email in emails
	])
	length = len(counts)
	# Create a domain mapping
	domains = defaultdict(generator.domain_name)

	for idx, (domain, count) in enumerate(counts.most_common()):

		if (count*100.0)/length > 5 and count > 10:
			# Whitelist the domain
			domains[domain] = domain
		else:
			# Create a fake domain
			domains[domain]

	return domains  
	
def fuzzy_profile(domains, name=None, email=None):
	"""
	Return a profile that allows for fuzzy names and emails.
	"""
	parts = fuzzy_name_parts()
	return {
		"names": {name: fuzzy_name(parts, name)},
		"emails": {email: fuzzy_email(domains, parts, email)},
	}

def fuzzy_name_parts():
	"""
	Returns first, middle, and last name parts
	"""
	return (
		generator.first_name(),
		generator.first_name(),
		generator.last_name()
	)

def fuzzy_name(parts, name=None):
	"""
	Creates a name that has a similar case to the passed in name.
	"""
	# Extract the first, initial, and last name from the parts.
	first, middle, last = parts

	# Create the name, with chance of middle or initial included.
	chance = generator.random_digit()
	if chance < 2:
		fname = u"{} {}. {}".format(first, middle[0], last)
	elif chance < 4:
		fname = u"{} {} {}".format(first, middle, last)
	else:
		fname = u"{} {}".format(first, last)

	if name is not None:
		# Match the capitalization of the name
		if name.isupper(): return fname.upper()
		if name.islower(): return fname.lower()
		if name.istitle(): return fname.title()

	return fname

def fuzzy_email(domains, parts, email=None):
	"""
	Creates an email similar to the name and original email.
	"""
	# Extract the first, initial, and last name from the parts.
	first, middle, last = parts

	# Use the domain mapping to identify the fake domain.
	if email is not None:
		domain = domains[email.split("@")[-1]]
	else:
		domain = generator.domain_name()

	# Create the username based on the name parts
	chance = generator.random_digit()
	if chance < 2:
		username = u"{}.{}".format(first, last)
	elif chance < 3:
		username = u"{}.{}.{}".format(first, middle[0], last)
	elif chance < 6:
		username = u"{}{}".format(first[0], last)
	elif chance < 8:
		username = last
	else:
		username = u"{}{}".format(
			first, generator.random_number()
		)

	# Match the case of the email
	if email is not None:
		if email.islower(): username = username.lower()
		if email.isupper(): username = username.upper()
	else:
		username = username.lower()

	return u"{}@{}".format(username, domain)

def test_ownership(name, email):
	parts = (name.lower()).split(" ")
	username = email.split("@")[0]
	usernames =[parts[0]]
	if len(parts)> 1:
		usernames = usernames  +[
		parts[1],
		"{}{}".format(parts[0], parts[1]),
		"{}.{}".format(parts[0], parts[1]),
		"{}_{}".format(parts[0], parts[1]),
		"{}{}".format(parts[1], parts[0]),
		"{}.{}".format(parts[1], parts[0]),
		"{}_{}".format(parts[1], parts[1]),
		"{}{}".format(parts[0], parts[1][0]),
		"{}.{}".format(parts[0], parts[1][0]),
		"{}_{}".format(parts[0], parts[1][0]),
		"{}{}".format(parts[1], parts[0][0]),
		"{}.{}".format(parts[1], parts[0][0]),
		"{}_{}".format(parts[1], parts[1][0]),
		"{}{}".format(parts[0][0], parts[1]),
		"{}.{}".format(parts[0][0], parts[1]),
		"{}_{}".format(parts[0][0], parts[1]),
		"{}{}".format(parts[1][0], parts[0]),
		"{}.{}".format(parts[1][0], parts[0]),
		"{}_{}".format(parts[1][0], parts[0])
		]
	if len(parts)>2:
		usernames = usernames +[
		parts[2],
		"{}{}".format(parts[2], parts[1]),
		"{}.{}".format(parts[2], parts[1]),
		"{}..{}".format(parts[0][0], parts[1]),
		"{}..{}".format(parts[0][0], parts[2]),
		"{}_{}".format(parts[2], parts[1]),
		"{}{}".format(parts[1], parts[2]),
		"{}.{}".format(parts[1], parts[2]),
		"{}_{}".format(parts[1], parts[1]),
		"{}{}".format(parts[2], parts[1][0]),
		"{}.{}".format(parts[2], parts[1][0]),
		"{}_{}".format(parts[2], parts[1][0]),
		"{}{}".format(parts[1], parts[2][0]),
		"{}.{}".format(parts[1], parts[2][0]),
		"{}_{}".format(parts[1], parts[1][0]),
		"{}{}".format(parts[2][0], parts[1]),
		"{}.{}".format(parts[2][0], parts[1]),
		"{}_{}".format(parts[2][0], parts[1]),
		"{}{}".format(parts[1][0], parts[2]),
		"{}.{}".format(parts[1][0], parts[2]),
		"{}_{}".format(parts[1][0], parts[2]),
		"{}{}".format(parts[0], parts[2]),
		"{}.{}".format(parts[0], parts[2]),
		"{}_{}".format(parts[0], parts[2]),
		"{}{}".format(parts[2], parts[0]),
		"{}.{}".format(parts[2], parts[0]),
		"{}_{}".format(parts[2], parts[2]),
		"{}{}".format(parts[0], parts[2][0]),
		"{}.{}".format(parts[0], parts[2][0]),
		"{}_{}".format(parts[0], parts[2][0]),
		"{}{}".format(parts[2], parts[0][0]),
		"{}.{}".format(parts[2], parts[0][0]),
		"{}_{}".format(parts[2], parts[2][0]),
		"{}{}".format(parts[0][0], parts[2]),
		"{}.{}".format(parts[0][0], parts[2]),
		"{}_{}".format(parts[0][0], parts[2]),
		"{}{}".format(parts[2][0], parts[0]),
		"{}.{}".format(parts[2][0], parts[0]),
		"{}_{}".format(parts[2][0], parts[0])
		]
		
	return (username in usernames)
		