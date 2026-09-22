from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from relationships.models import RelationshipEdge
from users.models import Person, UserAccount

# The same family used throughout manual verification this session and in
# kinverse-project's seed_sample.sql - kept in sync deliberately so a bug
# reproduced by hand and a bug caught by this suite are talking about the
# same tree:
#
#            Ramesh == Lakshmi
#               |
#   +-----------+-----------+
#   |                       |
# John == Mary          Deepa
#   |                       |
#   +--------+--------+   Kiran
#   |                 |
# Sunil == Priya    (no other kids)
#   |
#   +--------+
#   |        |
# Arjun   Meera


async def seed_sample_tree(session: AsyncSession) -> dict[str, Person | UserAccount]:
    sunil_account = UserAccount(email="sunil@example.com", auth_provider="email", status="active")
    session.add(sunil_account)
    await session.flush()

    people = {}
    for key, first, last, account in [
        ("ramesh", "Ramesh", "Kumar", None),
        ("lakshmi", "Lakshmi", "Kumar", None),
        ("john", "John", "Smith", None),
        ("mary", "Mary", "Smith", None),
        ("deepa", "Deepa", "Rao", None),
        ("sunil", "Sunil", "Narayanan", sunil_account),
        ("priya", "Priya", "Narayanan", None),
        ("arjun", "Arjun", "Narayanan", None),
        ("meera", "Meera", "Narayanan", None),
        ("kiran", "Kiran", "Rao", None),
    ]:
        person = Person(first_name=first, last_name=last)
        if account is not None:
            person.user_account = account
        session.add(person)
        people[key] = person
    await session.flush()

    def partner_edge(a: Person, b: Person, partner_type: str = "spouse") -> RelationshipEdge:
        lo, hi = (a, b) if str(a.id) < str(b.id) else (b, a)
        return RelationshipEdge(
            person_a_id=lo.id, person_b_id=hi.id, edge_type="partner",
            partner_type=partner_type, status="confirmed",
        )

    def parent_edge(parent: Person, child: Person) -> RelationshipEdge:
        return RelationshipEdge(
            person_a_id=parent.id, person_b_id=child.id, edge_type="parent_child", status="confirmed",
        )

    edges = [
        partner_edge(people["ramesh"], people["lakshmi"]),
        partner_edge(people["john"], people["mary"]),
        partner_edge(people["sunil"], people["priya"]),
        parent_edge(people["ramesh"], people["john"]),
        parent_edge(people["lakshmi"], people["john"]),
        parent_edge(people["ramesh"], people["deepa"]),
        parent_edge(people["lakshmi"], people["deepa"]),
        parent_edge(people["john"], people["sunil"]),
        parent_edge(people["mary"], people["sunil"]),
        parent_edge(people["sunil"], people["arjun"]),
        parent_edge(people["priya"], people["arjun"]),
        parent_edge(people["sunil"], people["meera"]),
        parent_edge(people["priya"], people["meera"]),
        parent_edge(people["deepa"], people["kiran"]),
    ]
    session.add_all(edges)
    await session.commit()

    for p in people.values():
        await session.refresh(p)

    return {**people, "sunil_account": sunil_account}
