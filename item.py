from datetime import datetime

class Item:
    def __init__(self, name, quantity, category):
        self.name = name
        self.quantity = quantity
        self.category = category
        self.last_accessed = datetime.now()  # automatically set to current time

    def __str__(self):
        return (f"{self.name} | "
                f"Qty: {self.quantity} | "
                f"Category: {self.category} | "
                f"Last Accessed: {self.last_accessed.strftime('%Y-%m-%d %H:%M')}")
    
    def to_dict(self):
        return{
            "name": self.name,
            "quantity": self.quantity,
            "category": self.category,
            "last_accessed": self.last_accessed.strftime('%Y-%m-%d %H:%M')

        }
    
    @classmethod
    def from_dict(cls,data):
        item = cls(data["name"], data["quantity"], data["category"])
        item.last_accessed = datetime.strptime(data["last_accessed"], '%Y-%m-%d %H:%M')
        return item
    

    def __str__(self):
        return (f"{self.name} | "
                f"Qty: {self.quantity} | "
                f"Category: {self.category} | "
                f"Last Accessed: {self.last_accessed.strftime('%Y-%m-%d %H:%M')}")