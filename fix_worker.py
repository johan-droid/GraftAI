with open("backend/worker.py", "r") as f:
    lines = f.readlines()

with open("backend/worker.py", "w") as f:
    for line in lines:
        if "if email_type == \"confirmation\":" in line:
            f.write(line.replace("                if", "            if"))
        elif "                await notify_event_created" in line:
            f.write(line.replace("                await", "                await"))
        elif "                    else:" in line:
            f.write(line.replace("                    else:", "                else:"))
        else:
            f.write(line)
