type Task = { id: string; node: string; params: any; origin?: "ai" | "web2" | "bridge"; };

const queue: Task[] = [];

export async function queueTask(t: Task) {
  queue.push(t);
  console.log(`[QUEUE] Task added: ${t.id} (${t.node})`);
}

export function getPending() {
  return queue.filter(q => q);
}
