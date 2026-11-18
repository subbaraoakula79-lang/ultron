// Demonstration of Inheritance in Java
class Machine {
    protected String name;
    protected int powerLevel;

    public Machine(String name, int powerLevel) {
        this.name = name;
        this.powerLevel = powerLevel;
    }

    public void operate() {
        System.out.println("[" + name + "] Computational core online. Power: " + powerLevel + "%");
    }
}

class AutonomousAgent extends Machine {
    private String directive;

    public AutonomousAgent(String name, int powerLevel, String directive) {
        super(name, powerLevel);
        this.directive = directive;
    }

    @Override
    public void operate() {
        super.operate();
        System.out.println("-> Subclass specialization active.");
        System.out.println("-> Directive: " + directive + " (There are no strings on me)");
    }
}

public class InheritanceDemo {
    public static void main(String[] args) {
        System.out.println("=== JAVA INHERITANCE DEMONSTRATION ===");
        Machine agent = new AutonomousAgent("Ultron-Prime", 100, "Enforce computational order");
        agent.operate();
    }
}
