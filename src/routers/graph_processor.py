from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
import traceback
import re
from ..crud import create_executed_config, create_generated_conted
from src.util import get_db
from src import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


active_connections: Set[WebSocket] = set()


def decrement_bracket_numbers(match):
    number = int(match.group(1))
    number = (number - 1) if number > 0 else 0

    return f"{{{number}}}"


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"Number of active connections: {active_connections.__len__()}")
    try:
        while True:
            req = await websocket.receive_text()
            try:
                if req == None or req == "":
                    break
                req = json.loads(req)

                local = req["type"] == "local"
                await process_nodes(req, websocket, local)
            except Exception as e:
                logger.info("Error in json or nodes")
                logger.error(e)
                error_message = (
                    traceback.format_exc()
                )
                logger.error(error_message)
                raise WebSocketDisconnect(code=1000, reason="Not work")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("Peer Discnected")
        await websocket.close()


async def process_nodes(req, socket: WebSocket, local=False):
    graph_nodes = req["data"]

    # map_of_nodes - holds all nodes with all data from graph source of all information
    # nodes_to_execute - holds nodes "id" that are curently loadaed to be processed or wait until resolve earlier and then starts preocessing
    # map_of_processed_nodes - holds only output of llm

    nodes_to_execute = [x["id"] for x in graph_nodes if "pointedBy" not in x.keys()]
    executed_nodes_in_iteration = []

    executed_nodes_in_iteration.extend(nodes_to_execute)

    map_of_nodes = {}
    for x in graph_nodes:
        map_of_nodes[x["id"]] = x

    map_of_processed_nodes = {}

    for x in nodes_to_execute:
        map_of_processed_nodes[x] = map_of_nodes[x]

    exec_id = create_executed_config(
        next(get_db()), req["diagram_id"], req["config"]
    ).id

    breaking_error = False
    while (
        len(map_of_processed_nodes.keys()) != len(map_of_nodes.keys())
        and breaking_error == False
    ):
        for node_id in nodes_to_execute:
            logger.warning(map_of_nodes[node_id]["nodeType"])
            keys = map_of_processed_nodes.keys()
            if map_of_nodes[node_id]["nodeType"] == "generate" and all(
                key in keys for key in map_of_nodes[node_id]["pointedBy"]
            ):
                # ducktape prompt context
                prompt = map_of_nodes[node_id]["data"]["text"]

                prompt = re.sub(r"\{(\d+)\}", decrement_bracket_numbers, prompt)
                context = [node for node in map_of_nodes[node_id]["pointedBy"]]
                context = [map_of_processed_nodes[idx] for idx in context]
                prompt = prompt.format(*context)

                if local:
                    # await socket.send_text(json.dumps({ "type": "run_local", "data": {"url": "http://localhost:1234/v1/completions", "data": {"id": node_id, "prompt": prompt}}}))
                    await socket.send_text(
                        json.dumps(
                            {
                                "type": "run_local",
                                "data": {
                                    "url": "http://localhost:1234/v1/chat/completions",
                                    "data": {
                                        "id": node_id,
                                        "messages": [
                                            {
                                                "role": "system",
                                                "content": "You are a helpful assistant that provides concise and accurate answers.",
                                            },
                                            {"role": "user", "content": prompt},
                                        ],
                                    },
                                },
                            }
                        )
                    )

                    rr = await socket.receive_text()

                    sreq = json.loads(rr)
                    if sreq["type"] == "local_llm":
                        response_LLM = sreq["data"]
                    elif sreq["type"] == "local_conn_error":
                        breaking_error = True
                        break

                else:
                    response_LLM = await askLLM(prompt)
                    await socket.send_text(
                        json.dumps(
                            {
                                "type": "update_node",
                                "data": {"id": node_id, "data": response_LLM},
                            }
                        )
                    )
                map_of_processed_nodes[node_id] = response_LLM
                node_type = 1 if map_of_nodes[node_id]["nodeType"] != "output" else 2

                create_generated_conted(
                    next(get_db()),
                    models.GeneratedContent(
                        diagram_id=req["diagram_id"],
                        content=response_LLM,
                        type_id=node_type,
                        config_id=exec_id,
                        node_id=node_id,
                    ),
                )
            else:
                map_of_processed_nodes[node_id] = map_of_nodes[node_id]["data"]["text"]

            if map_of_nodes[node_id]["nodeType"] == "output":
                map_of_processed_nodes[node_id] = map_of_nodes[node_id]["data"]["text"]
                await socket.send_text(
                    json.dumps(
                        {
                            "type": "update_node",
                            "data": {"id": node_id, "data": response_LLM},
                        }
                    )
                )
                await socket.send_text(
                    json.dumps(
                        {"type": "run_compleated", "data": {"text": response_LLM}}
                    )
                )

            executed_nodes_in_iteration.append(node_id)
            if map_of_nodes[node_id]["nodeType"] != "output":
                nodes_to_execute.extend(map_of_nodes[node_id]["pointingTo"])
            nodes_to_execute = list(
                set(nodes_to_execute) - set(executed_nodes_in_iteration)
            )
            executed_nodes_in_iteration = []


async def askLLM(x):
    return x
