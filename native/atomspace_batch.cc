// Bounded Atoms/Values transport, not an admission authority or Atomese evaluator.
#include <opencog/atomspace/AtomSpace.h>
#include <opencog/atoms/base/Node.h>
#include <opencog/atoms/base/Link.h>
#include <opencog/atoms/value/FloatValue.h>
#include <opencog/atoms/value/StringValue.h>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>

using namespace opencog;

static std::string hex(const std::string& s) {
    if (s.empty()) return "-";
    const char* digits = "0123456789abcdef";
    std::string out;
    for (unsigned char c : s) { out += digits[c >> 4]; out += digits[c & 15]; }
    return out;
}
static std::string unhex(const std::string& s) {
    if (s == "-") return "";
    if (s.empty() || s.size() % 2 || s.size() > 131072)
        throw std::runtime_error("invalid hex length");
    std::string out;
    auto digit = [](char c) {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        throw std::runtime_error("invalid hex digit");
    };
    for (size_t i = 0; i < s.size(); i += 2)
        out += char(16 * digit(s[i]) + digit(s[i+1]));
    return out;
}
template<class T> static T take(std::istringstream& in) {
    T x;
    if (!(in >> x)) throw std::runtime_error("missing or invalid field");
    return x;
}
int main() {
    try {
        AtomSpace space;
        std::vector<Handle> refs;
        std::map<Handle, size_t> canonical;
        std::map<std::pair<Handle, Handle>, char> values;
        std::string line;
        size_t bytes = 0, commands = 0;
        while (std::getline(std::cin, line)) {
            bytes += line.size();
            if (++commands > 100000 || bytes > 8388608)
                throw std::runtime_error("batch limit exceeded");
            std::istringstream in(line);
            auto op = take<std::string>(in);
            if (op == "N" || op == "P" || op == "L") {
                Handle atom;
                if (op != "L") atom = space.add_node(
                    op == "N" ? CONCEPT_NODE : PREDICATE_NODE,
                    unhex(take<std::string>(in)));
                else {
                    auto count = take<size_t>(in);
                    if (count > 4096) throw std::runtime_error("arity limit");
                    HandleSeq outgoing;
                    for (size_t i = 0; i < count; ++i)
                        outgoing.push_back(refs.at(take<size_t>(in)));
                    atom = space.add_link(LIST_LINK, std::move(outgoing));
                }
                canonical.emplace(atom, refs.size());
                refs.push_back(atom);
            } else if (op == "S" || op == "F") {
                auto atom = refs.at(take<size_t>(in));
                auto key = refs.at(take<size_t>(in));
                if (key->get_type() != PREDICATE_NODE)
                    throw std::runtime_error("value key must be a PredicateNode");
                if (op == "S") space.set_value(atom, key,
                    std::make_shared<StringValue>(unhex(take<std::string>(in))));
                else {
                    auto count = take<size_t>(in);
                    if (count > 4096) throw std::runtime_error("value limit");
                    std::vector<double> data;
                    for (size_t i = 0; i < count; ++i) {
                        double d = take<double>(in);
                        if (!std::isfinite(d)) throw std::runtime_error("nonfinite value");
                        data.push_back(d);
                    }
                    space.set_value(atom, key, std::make_shared<FloatValue>(data));
                }
                values[{atom, key}] = op[0];
            } else throw std::runtime_error("unknown command");
            std::string extra;
            if (in >> extra) throw std::runtime_error("trailing fields");
        }
        // Read back from the actual AtomSpace, including canonical handles,
        // ordered outgoing sets and the final value after any overwrites.
        std::cout << "reachability-atomspace-batch/v1 " << ATOMSPACE_PIN << '\n';
        for (size_t i = 0; i < refs.size(); ++i) {
            auto atom = space.get_atom(refs[i]);
            std::cout << "A " << i << ' ' << canonical.at(atom) << ' ';
            if (atom->get_type() == LIST_LINK) {
                auto link = LinkCast(atom);
                std::cout << "L " << link->get_arity();
                for (const auto& h : link->getOutgoingSet())
                    std::cout << ' ' << canonical.at(h);
            } else std::cout << (atom->get_type() == CONCEPT_NODE ? "N " : "P ")
                             << hex(atom->get_name());
            std::cout << '\n';
        }
        std::cout << std::setprecision(17);
        for (const auto& entry : values) {
            const auto& atom = entry.first.first;
            const auto& key = entry.first.second;
            auto value = atom->getValue(key);
            std::cout << entry.second << ' ' << canonical.at(atom) << ' ' << canonical.at(key);
            if (entry.second == 'S')
                std::cout << ' ' << hex(StringValueCast(value)->value().at(0));
            else {
                const auto& data = FloatValueCast(value)->value();
                std::cout << ' ' << data.size();
                for (double d : data) std::cout << ' ' << d;
            }
            std::cout << '\n';
        }
        std::cout << "SIZE " << space.get_size() << '\n';
    } catch (const std::exception& e) {
        std::cerr << "AtomSpace batch rejected: " << e.what() << '\n';
        return 1;
    }
}
