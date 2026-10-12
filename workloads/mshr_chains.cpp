// A small, deterministic memory-level-parallelism experiment.
// Each node occupies one cache line. Both modes visit all 32768 nodes once
// per traversal; the difference is one dependency chain versus eight.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <numeric>
#include <vector>

#ifdef USE_GEM5_OPS
#include <gem5/m5ops.h>
#endif

namespace {

constexpr std::uint32_t kNodes = 32768;  // 2 MiB at 64 bytes per node.
constexpr std::uint32_t kStreams = 8;
constexpr std::uint32_t kMeasuredPasses = 2;
constexpr std::uint64_t kSeed = 0x123456789abcdef0ULL;

struct alignas(64) Node {
    std::uint32_t next;
    std::uint8_t padding[60]{};
};
static_assert(sizeof(Node) == 64, "one node must occupy one cache line");

std::uint64_t random_word(std::uint64_t& state) {
    state += 0x9e3779b97f4a7c15ULL;
    std::uint64_t value = state;
    value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
    value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
    return value ^ (value >> 31);
}

using Cursors = std::array<std::uint32_t, kStreams>;

__attribute__((noinline)) std::uint32_t traverse_one(
    const Node* nodes, std::uint32_t cursor) {
    for (std::uint32_t i = 0; i < kNodes; ++i) {
        cursor = nodes[cursor].next;
    }
    return cursor;
}

__attribute__((noinline)) Cursors traverse_eight(
    const Node* nodes, Cursors cursor) {
    for (std::uint32_t i = 0; i < kNodes / kStreams; ++i) {
        cursor[0] = nodes[cursor[0]].next;
        cursor[1] = nodes[cursor[1]].next;
        cursor[2] = nodes[cursor[2]].next;
        cursor[3] = nodes[cursor[3]].next;
        cursor[4] = nodes[cursor[4]].next;
        cursor[5] = nodes[cursor[5]].next;
        cursor[6] = nodes[cursor[6]].next;
        cursor[7] = nodes[cursor[7]].next;
    }
    return cursor;
}

void fail(const char* message) {
    std::fprintf(stderr, "ERROR: %s\n", message);
    std::exit(1);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2 || (std::strcmp(argv[1], "dependent") != 0 &&
                      std::strcmp(argv[1], "independent") != 0)) {
        std::fprintf(stderr, "usage: %s dependent|independent\n", argv[0]);
        return 2;
    }
    const bool independent = std::strcmp(argv[1], "independent") == 0;
    std::vector<Node> nodes(kNodes);
    std::vector<std::uint32_t> order(kNodes);
    std::iota(order.begin(), order.end(), 0);
    std::uint64_t state = kSeed;
    for (std::uint32_t i = kNodes - 1; i > 0; --i) {
        const std::uint32_t j = random_word(state) % (i + 1);
        const std::uint32_t tmp = order[i];
        order[i] = order[j];
        order[j] = tmp;
    }

    Cursors heads{};
    const std::uint32_t streams = independent ? kStreams : 1;
    const std::uint32_t chain_length = kNodes / streams;
    for (std::uint32_t stream = 0; stream < streams; ++stream) {
        const std::uint32_t begin = stream * chain_length;
        heads[stream] = order[begin];
        for (std::uint32_t i = 0; i < chain_length; ++i) {
            const std::uint32_t here = order[begin + i];
            const std::uint32_t next = order[begin + ((i + 1) % chain_length)];
            nodes[here].next = next;
        }
    }

    // Check that every node belongs to exactly one intended ring.
    std::vector<std::uint8_t> seen(kNodes, 0);
    for (std::uint32_t stream = 0; stream < streams; ++stream) {
        std::uint32_t cursor = heads[stream];
        for (std::uint32_t i = 0; i < chain_length; ++i) {
            if (cursor >= kNodes || seen[cursor] != 0) fail("invalid ring");
            seen[cursor] = 1;
            cursor = nodes[cursor].next;
        }
        if (cursor != heads[stream]) fail("ring does not close");
    }

    // Warm-up changes cache state, but its statistics are discarded.
    Cursors cursor = heads;
    cursor = independent ? traverse_eight(nodes.data(), cursor)
                         : Cursors{traverse_one(nodes.data(), cursor[0])};
    if (cursor != heads) fail("warm-up result differs from expected");

#ifdef USE_GEM5_OPS
    m5_reset_stats(0, 0);
#endif
    for (std::uint32_t pass = 0; pass < kMeasuredPasses; ++pass) {
        cursor = independent ? traverse_eight(nodes.data(), cursor)
                             : Cursors{traverse_one(nodes.data(), cursor[0])};
    }
#ifdef USE_GEM5_OPS
    m5_dump_stats(0, 0);
#endif
    if (cursor != heads) fail("measured result differs from expected");

    std::uint64_t checksum = 0;
    for (std::uint32_t stream = 0; stream < streams; ++stream) {
        checksum += static_cast<std::uint64_t>(stream + 1) * cursor[stream];
    }
    std::printf("RESULT mode=%s checksum=%llu loads=%u passes=%u nodes=%u seed=%llu\n",
                argv[1], static_cast<unsigned long long>(checksum),
                kNodes * kMeasuredPasses, kMeasuredPasses, kNodes,
                static_cast<unsigned long long>(kSeed));
    return 0;
}
