print("Step 1: Import supervisor module")
import workflow_agents.supervisor as sup_module
print(f"  supervisor module loaded: {sup_module}")

print("\nStep 2: Check if create_supervisor_graph exists")
print(f"  create_supervisor_graph: {hasattr(sup_module, 'create_supervisor_graph')}")

print("\nStep 3: Check workflow_supervisor value")
print(f"  workflow_supervisor value: {sup_module.workflow_supervisor}")
print(f"  Type: {type(sup_module.workflow_supervisor)}")

print("\nStep 4: Try calling create_supervisor_graph directly")
graph = sup_module.create_supervisor_graph()
print(f"  Direct call result type: {type(graph)}")
print(f"  Direct call result: {graph}")
