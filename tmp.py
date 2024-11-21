fruits = [
	{'name':'apple','price':2.45},
	{'name':'banana','price':3.18},
	{'name':'oranges','price':1.87},
]

foo  = { x['name']:x['price'] for x in fruits if x['price']>=2 }

print( foo )













