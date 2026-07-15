import ml_server
print("Force training Attendance...")
try: ml_server.train_attendance()
except Exception as e: print(e)

print("Force training Availability...")
try: ml_server.train_availability()
except Exception as e: print(e)

print("Force training Demand...")
try: ml_server.train_demand()
except Exception as e: print(e)

print("Force training Skill...")
try: ml_server.train_skill()
except Exception as e: print(e)

print("Force training Fraud...")
try: ml_server.train_fraud()
except Exception as e: print(e)

print("Force training Wage...")
try: ml_server.train_wage()
except Exception as e: print(e)

print("Done training all models.")
