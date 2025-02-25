import json
from datetime import datetime, timedelta  # Am adăugat timedelta aici

# Listele predefinite rămân la fel
CLIENTI_PREDEFINITI = [
    "Client A",
    "Client B",
    "Client C",
    "Client D"
]

PROIECTE_PREDEFINITE = [
    "Website nou",
    "Mentenanță",
    "Consultanță",
    "Training",
    "Dezvoltare aplicație"
]

ACTIVITATI_PREDEFINITE = [
    "Programare",
    "Meeting cu clientul",
    "Documentație",
    "Testing",
    "Code review",
    "Analiză cerințe",
    "Training"
]

class EmployeeActivity:
    def __init__(self):
        self.activities = []
        self.filename = "activities.json"
        self.load_activities()

    # ... toate metodele existente rămân la fel ...

    def get_date_range(self, range_type, date_string):
        """
        Această funcție calculează intervalul de date pentru săptămână sau lună.
        """
        date = datetime.strptime(date_string, '%Y-%m-%d')
        
        if range_type == "week":
            start_date = date - timedelta(days=date.weekday())
            end_date = start_date + timedelta(days=6)
        else:  # month
            start_date = date.replace(day=1)
            if date.month == 12:
                end_date = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
        
        return start_date, end_date

    def generate_period_report(self, start_date, end_date):
        """
        Această funcție generează un raport pentru o perioadă specifică.
        """
        period_activities = []
        total_hours = 0
        hours_per_client = {}
        hours_per_project = {}
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        for activity in self.activities:
            activity_date = datetime.strptime(activity['date'], '%Y-%m-%d')
            if start_str <= activity['date'] <= end_str:
                period_activities.append(activity)
                hours = activity['hours']
                total_hours += hours
                
                client = activity['client']
                hours_per_client[client] = hours_per_client.get(client, 0) + hours
                
                project = activity['project']
                hours_per_project[project] = hours_per_project.get(project, 0) + hours
        
        return {
            'activities': period_activities,
            'total_hours': total_hours,
            'hours_per_client': hours_per_client,
            'hours_per_project': hours_per_project,
            'start_date': start_str,
            'end_date': end_str
        }

    def save_activities(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.activities, f, indent=4, ensure_ascii=False)
        print("Activitățile au fost salvate în fișier!")

    def load_activities(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.activities = json.load(f)
        except FileNotFoundError:
            self.activities = []

    def choose_from_list(self, items, item_type):
        print(f"\nAlege {item_type} din lista următoare:")
        for idx, item in enumerate(items, 1):
            print(f"{idx}. {item}")
        print(f"{len(items) + 1}. Altă opțiune (introducere liberă)")
        
        while True:
            try:
                choice = int(input(f"\nAlege numărul pentru {item_type}: "))
                if 1 <= choice <= len(items):
                    return items[choice - 1]
                elif choice == len(items) + 1:
                    return input(f"Introdu {item_type} (text liber): ")
                else:
                    print("Opțiune invalidă!")
            except ValueError:
                print("Te rog introdu un număr valid!")

    def add_activity(self, date, client, project, activity_type, achievements, challenges, hours):
        activity = {
            "date": date,
            "client": client,
            "project": project,
            "activity_type": activity_type,
            "achievements": achievements,
            "challenges": challenges,
            "hours": hours
        }
        self.activities.append(activity)
        self.save_activities()
        print("Activitate adăugată cu succes!")

    def view_activities(self):
        if not self.activities:
            print("Nu există activități înregistrate.")
            return
        
        for activity in self.activities:
            print("\n--- Activitate ---")
            print(f"Data: {activity['date']}")
            print(f"Client: {activity['client']}")
            print(f"Proiect: {activity['project']}")
            print(f"Tip activitate: {activity['activity_type']}")
            print(f"Realizări: {activity['achievements']}")
            print(f"Provocări: {activity['challenges']}")
            print(f"Ore lucrate: {activity['hours']}")

    def calculate_hours(self, calculation_type):
        total_hours = {}
        
        for activity in self.activities:
            key = activity[calculation_type]
            hours = activity["hours"]
            
            if key in total_hours:
                total_hours[key] += hours
            else:
                total_hours[key] = hours
        
        return total_hours

def validate_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def main():
    tracker = EmployeeActivity()
    
    while True:
        print("\n=== Meniu ===")
        print("1. Adaugă activitate nouă")
        print("2. Vezi toate activitățile")
        print("3. Caută activități")
        print("4. Vezi raport ore")
        print("5. Ieșire")
        
        choice = input("Alege o opțiune (1-5): ")
        
        if choice == "1":
            while True:
                date = input("Data (YYYY-MM-DD): ")
                if validate_date(date):
                    break
                print("Format dată invalid!")
            
            client = tracker.choose_from_list(CLIENTI_PREDEFINITI, "client")
            project = tracker.choose_from_list(PROIECTE_PREDEFINITE, "proiect")
            activity_type = tracker.choose_from_list(ACTIVITATI_PREDEFINITE, "tip activitate")
            
            while True:
                try:
                    hours = float(input("Număr ore lucrate: "))
                    if hours > 0:
                        break
                    print("Numărul de ore trebuie să fie pozitiv!")
                except ValueError:
                    print("Te rog introdu un număr valid!")
            
            achievements = input("Ce ai realizat azi? ")
            challenges = input("Ce provocări ai întâmpinat? ")
            
            tracker.add_activity(date, client, project, activity_type, achievements, challenges, hours)
            
        elif choice == "2":
            tracker.view_activities()
            
        elif choice == "3":
            print("\n=== Caută Activități ===")
            print("1. Caută după dată")
            print("2. Caută după client")
            
            search_choice = input("Alege opțiunea de căutare (1-2): ")
            
            if search_choice == "1":
                date = input("Introdu data (YYYY-MM-DD): ")
                if validate_date(date):
                    results = tracker.search_activities("date", date)
                else:
                    print("Format dată invalid!")
                    continue
            elif search_choice == "2":
                client = input("Introdu numele clientului: ")
                results = tracker.search_activities("client", client)
            else:
                print("Opțiune invalidă!")
                continue
            
            if results:
                print("\nActivități găsite:")
                for activity in results:
                    print("\n--- Activitate ---")
                    print(f"Data: {activity['date']}")
                    print(f"Client: {activity['client']}")
                    print(f"Proiect: {activity['project']}")
                    print(f"Tip activitate: {activity['activity_type']}")
                    print(f"Ore lucrate: {activity['hours']}")
                    print(f"Realizări: {activity['achievements']}")
                    print(f"Provocări: {activity['challenges']}")
            else:
                print("Nu s-au găsit activități care să corespundă criteriilor de căutare.")
                
        elif choice == "4":
            print("\n=== Rapoarte ===")
            print("1. Total ore pe client")
            print("2. Total ore pe proiect")
            print("3. Raport săptămânal")
            print("4. Raport lunar")
            
            report_choice = input("Alege tipul de raport (1-4): ")
            
            if report_choice in ["1", "2"]:
                if report_choice == "1":
                    total_hours = tracker.calculate_hours("client")
                    print("\nTotal ore pe client:")
                    for client, hours in total_hours.items():
                        print(f"{client}: {hours} ore")
                else:
                    total_hours = tracker.calculate_hours("project")
                    print("\nTotal ore pe proiect:")
                    for project, hours in total_hours.items():
                        print(f"{project}: {hours} ore")
            
            elif report_choice in ["3", "4"]:
                date = input("Introdu o dată din perioada dorită (YYYY-MM-DD): ")
                if not validate_date(date):
                    print("Format dată invalid!")
                    continue
                
                report_type = "week" if report_choice == "3" else "month"
                start_date, end_date = tracker.get_date_range(report_type, date)
                
                report = tracker.generate_period_report(start_date, end_date)
                
                print(f"\n=== Raport {report_type == 'week' and 'săptămânal' or 'lunar'} ===")
                print(f"Perioada: {report['start_date']} - {report['end_date']}")
                print(f"Total ore lucrate: {report['total_hours']}")
                
                print("\nOre pe client:")
                for client, hours in report['hours_per_client'].items():
                    print(f"  {client}: {hours} ore")
                
                print("\nOre pe proiect:")
                for project, hours in report['hours_per_project'].items():
                    print(f"  {project}: {hours} ore")
                
                print("\nActivități în perioada selectată:")
                for activity in report['activities']:
                    print(f"\n  Data: {activity['date']}")
                    print(f"  Client: {activity['client']}")
                    print(f"  Proiect: {activity['project']}")
                    print(f"  Tip activitate: {activity['activity_type']}")
                    print(f"  Ore: {activity['hours']}")
                    print(f"  Realizări: {activity['achievements']}")
            
            else:
                print("Opțiune invalidă!")
                
        elif choice == "5":
            print("La revedere!")
            break
            
        else:
            print("Opțiune invalidă. Te rog alege din nou.")

if __name__ == "__main__":
    main()